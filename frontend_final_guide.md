# 🛌 슬립캐시 수면 기능 프론트엔드 개발 가이드 (최종)

## 🎯 핵심 변경사항
**포인트 계산 방식이 프론트엔드 중심으로 변경되었습니다.**
- 프론트엔드가 타이머 기반으로 포인트 계산
- 서버는 획득 액션(중간 획득, 수면 종료) 시에만 포인트 기록
- 중간 획득 = 적립 포인트 + 10P 보너스

## 🔐 인증 정보
```
JWT Token: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsInVzZXJuYW1lIjoidGVzdHVzZXIiLCJlbWFpbCI6InRlc3RAc2xlZXBjYXNoLmNvbSIsImlhdCI6MTc2NTQyOTkyOSwiZXhwIjoxNzY1NTE2MzI5fQ.NHjmjXyqAwhIF6JpgGNSNV-1e9ticZ2iJaxXUMxCRh0

Database: sleep_cash (PostgreSQL)
Base URL: http://localhost:5000
```

## 📋 API 엔드포인트

### 1. 앱 시작 시 상태 확인
**GET** `/api/sleep/daily-status`

**응답:**
```json
{
  "success": true,
  "data": {
    "current_session": {
      "session_id": 19,
      "status": "running", 
      "elapsed_minutes": 15
    },
    "timer_points": {
      "claimed_points": 86.0,
      "remaining_limit": 78.5
    },
    "intermediate_points": {
      "claimed_count": 2,
      "remaining_claims": 3,
      "claimed_points": 35.5
    }
  }
}
```

### 2. 수면 세션 시작
**POST** `/api/sleep/start`

**요청:**
```json
{
  "mood": "good",
  "memo": "오늘 하루 좋았어",
  "white_noise_type": "rain",
  "white_noise_volume": 70
}
```

### 3. 수면 상태 조회 (실시간 폴링용)
**GET** `/api/sleep/status`

**응답:**
```json
{
  "success": true,
  "data": {
    "session_id": 19,
    "elapsed_minutes": 15,
    "timer_points": {
      "claimed_points": 86.0,
      "remaining_limit": 78.5
    },
    "intermediate_points": {
      "claimed_count": 2,
      "remaining_claims": 3
    }
  }
}
```

### 4. 중간 포인트 획득 ⭐️ 핵심 변경
**POST** `/api/sleep/claim-intermediate`

**요청:**
```json
{
  "accumulated_points": 15.5  // 프론트에서 계산한 적립 포인트
}
```

**응답:**
```json
{
  "success": true,
  "data": {
    "accumulated_points": 15.5,      // 적립 포인트
    "bonus_points": 10.0,            // 중간 획득 보너스
    "total_points_awarded": 25.5,    // 총 획득 (15.5 + 10)
    "new_total_points": 1229,        // 업데이트된 총 포인트
    "remaining_claims": 3            // 남은 중간 획득 횟수
  }
}
```

### 5. 수면 종료
**POST** `/api/sleep/end`

**응답:**
```json
{
  "success": true,
  "data": {
    "session_id": 19,
    "total_minutes": 60,
    "ended_at": "2025-12-11T07:30:00Z"
  }
}
```

### 6. 타이머 포인트 획득 (광고 시청) ⭐️ 핵심 변경
**POST** `/api/sleep/claim-timer`

**요청:**
```json
{
  "accumulated_points": 30.0  // 프론트에서 계산한 적립 포인트
}
```

**응답:**
```json
{
  "success": true,
  "data": {
    "accumulated_points": 30.0,      // 적립 포인트
    "ad_bonus_points": 10.0,         // 광고 보너스
    "total_claimed_points": 40.0,    // 총 획득 (30 + 10)
    "new_total_points": 1269         // 업데이트된 총 포인트
  }
}
```

## 💰 포인트 계산 로직 (프론트엔드 담당)

### 타이머 포인트 계산
```javascript
class SleepTimer {
  constructor() {
    this.startTime = new Date();
    this.accumulatedPoints = 0;
    this.currentSeconds = 59;
  }
  
  // 1초마다 실행
  tick() {
    this.currentSeconds--;
    
    if (this.currentSeconds <= 0) {
      // 1분 완료 → 0.5P 적립
      this.accumulatedPoints += 0.5;
      this.currentSeconds = 59;
      
      // UI 업데이트
      this.showPointIncrement(0.5);
      this.updateAccumulatedDisplay(this.accumulatedPoints);
    }
    
    // 타이머 UI 업데이트 (00:59 → 00:00)
    this.updateTimerDisplay(this.currentSeconds);
  }
  
  // 중간 획득 시 호출
  async claimIntermediate() {
    const response = await fetch('/api/sleep/claim-intermediate', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        accumulated_points: this.accumulatedPoints
      })
    });
    
    if (response.success) {
      // 적립 포인트 초기화 (이미 획득했으므로)
      this.accumulatedPoints = 0;
      
      // UI 업데이트
      this.updateUserTotalPoints(response.data.new_total_points);
      this.updateIntermediateButton(response.data.remaining_claims);
    }
  }
  
  // 수면 종료 시 호출
  async claimTimer() {
    const response = await fetch('/api/sleep/claim-timer', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        accumulated_points: this.accumulatedPoints
      })
    });
    
    if (response.success) {
      this.showClaimSuccess(response.data);
    }
  }
}
```

### 일일 한도 관리
```javascript
const checkDailyLimit = (currentTotal, newPoints) => {
  const DAILY_LIMIT = 200;
  
  if (currentTotal + newPoints > DAILY_LIMIT) {
    const available = DAILY_LIMIT - currentTotal;
    showError(`일일 한도 초과! 획득 가능: ${available}P`);
    return false;
  }
  
  return true;
};
```

## 🔄 앱 재시작 플로우

### 1. 앱 시작 시
```javascript
const initializeApp = async () => {
  const response = await fetch('/api/sleep/daily-status');
  
  if (response.data.current_session) {
    // 기존 세션 복원
    resumeSleepSession(response.data);
  } else {
    // 새 플로우 시작
    startSleepFlow();
  }
};
```

### 2. 세션 복원
```javascript
const resumeSleepSession = (data) => {
  const session = data.current_session;
  
  // 타이머 복원 (경과 시간부터 시작)
  const elapsedMinutes = session.elapsed_minutes;
  const currentSecond = (elapsedMinutes * 60) % 60;
  const startSecond = currentSecond === 0 ? 59 : (59 - currentSecond);
  
  // 적립 포인트는 0부터 시작 (이미 획득한 것은 서버에 기록됨)
  sleepTimer.accumulatedPoints = 0;
  sleepTimer.currentSeconds = startSecond;
  
  // UI 복원
  updateIntermediateButton(data.intermediate_points.remaining_claims);
  updateDailyLimits(data.timer_points.remaining_limit);
  
  // 타이머 재시작
  sleepTimer.start();
};
```

## 🎮 UI/UX 가이드

### 수면 화면 구성
```javascript
const SleepScreen = () => {
  return (
    <div className="sleep-screen">
      {/* 타이머 (00:59 → 00:00) */}
      <div className="timer">
        {formatTime(currentSeconds)}
      </div>
      
      {/* 적립 포인트 표시 */}
      <div className="accumulated-points">
        적립 중: {accumulatedPoints}P
      </div>
      
      {/* 중간 획득 버튼 */}
      <button 
        onClick={claimIntermediate}
        disabled={remainingClaims === 0}
        className="intermediate-claim-btn"
      >
        🎁 포인트 받기 ({remainingClaims}/5)
        <span>적립 {accumulatedPoints}P + 보너스 10P</span>
      </button>
      
      {/* 일일 한도 표시 */}
      <div className="daily-limit">
        오늘 획득 가능: {remainingLimit}P / 200P
      </div>
      
      {/* 수면 종료 버튼 */}
      <button onClick={endSleep}>수면 종료</button>
    </div>
  );
};
```

### 수면 종료 팝업
```javascript
const showEndPopup = () => {
  const popup = {
    title: "수면 완료!",
    content: `
      <div>
        <h3>적립된 포인트: ${accumulatedPoints}P</h3>
        <p>광고를 보시면 +10P 보너스!</p>
        <p class="total">총 획득 가능: ${accumulatedPoints + 10}P</p>
      </div>
    `,
    buttons: [
      {
        text: "광고 보고 포인트 받기",
        action: () => claimTimer()
      },
      {
        text: "포인트 없이 종료", 
        action: () => endWithoutClaim()
      }
    ]
  };
};
```

## 🚨 에러 처리

### 주요 에러 코드
```javascript
const handleApiError = (error) => {
  switch (error.code) {
    case 'NO_ACTIVE_SESSION':
      // 세션이 없음 → 새 세션 시작 유도
      showError('수면 세션을 다시 시작해주세요');
      break;
      
    case 'INTERMEDIATE_LIMIT_REACHED':
      // 중간 획득 한도 초과
      disableIntermediateButton();
      showInfo('오늘 중간 포인트를 모두 받았어요!');
      break;
      
    case 'DAILY_LIMIT_EXCEEDED':
      // 일일 한도 초과
      showError(error.message); // "일일 한도를 초과합니다. 획득 가능: XP"
      break;
      
    case 'ACTIVE_SESSION_EXISTS':
      // 이미 세션 있음 → 기존 세션으로 이동
      redirectToSleepScreen();
      break;
  }
};
```

## 🎯 핵심 포인트

### ⭐️ 중요한 변경사항
1. **프론트엔드가 포인트 계산**: 1분당 0.5P씩 `accumulatedPoints`에 누적
2. **중간 획득**: `accumulated_points` + 10P 보너스
3. **타이머 획득**: `accumulated_points` + 10P 광고 보너스
4. **획득 후 초기화**: 포인트 획득 시 `accumulatedPoints = 0`으로 리셋

### 📱 사용자 경험
- 타이머는 59초 → 0초 카운트다운
- 1분마다 +0.5P 시각적 효과
- 중간 획득 버튼에 예상 획득 포인트 표시
- 일일 한도 실시간 표시

### 🔄 동기화
- 30초마다 `/api/sleep/status` 호출로 서버 상태 확인
- 앱 재시작 시 `/api/sleep/daily-status`로 세션 복원
- 네트워크 오류 시 로컬 상태 유지

이제 프론트엔드에서 완전한 수면 기능을 구현할 수 있습니다!
