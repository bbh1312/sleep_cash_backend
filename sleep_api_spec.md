# 🛌 슬립캐시 수면 API 명세서 (중간 획득 포인트 포함)

## 🔐 인증
모든 API는 JWT 토큰 인증이 필요합니다.
```
Authorization: Bearer {JWT_TOKEN}
```

## 💰 포인트 시스템
- **타이머 포인트**: 1분당 0.5P, 최대 200P (pending → 광고 시청 → claimed)
- **중간 획득 포인트**: 1회당 10P, 최대 5회 (50P), 광고 시청 즉시 지급

## 📋 API 목록

### 1. 수면 세션 시작
**POST** `/api/sleep/start`

**Request Body:**
```json
{
  "mood": "good",           // 기분 (optional)
  "memo": "오늘 하루 좋았어", // 메모 (optional)
  "white_noise_type": "rain", // 백색소음 종류 (optional)
  "white_noise_volume": 50    // 백색소음 볼륨 (optional)
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": 123,
    "started_at": "2025-12-11T11:52:00Z",
    "status": "running"
  }
}
```

### 2. 수면 상태 조회
**GET** `/api/sleep/status`

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": 123,
    "started_at": "2025-12-11T11:52:00Z",
    "elapsed_minutes": 45,
    "timer_points": {
      "pending_points": 22.5,
      "claimed_points": 0.0,
      "daily_limit": 200,
      "remaining_limit": 177.5
    },
    "intermediate_points": {
      "claimed_count": 2,
      "claimed_points": 20.0,
      "max_claims": 5,
      "remaining_claims": 3,
      "points_per_claim": 10
    },
    "status": "running",
    "mood": "good",
    "white_noise_type": "rain",
    "white_noise_volume": 50
  }
}
```

### 3. 중간 포인트 획득 (NEW)
**POST** `/api/sleep/claim-intermediate`

**Response:**
```json
{
  "success": true,
  "data": {
    "claim_sequence": 3,
    "points_awarded": 10.0,
    "new_total_points": 1030,
    "remaining_claims": 2,
    "total_intermediate_points": 30.0
  }
}
```

**Error Response (한도 초과):**
```json
{
  "success": false,
  "error": {
    "code": "INTERMEDIATE_LIMIT_REACHED",
    "message": "오늘 중간 포인트 획득 한도에 도달했습니다. (5/5)"
  }
}
```

### 4. 수면 세션 종료
**POST** `/api/sleep/end`

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": 123,
    "total_minutes": 60,
    "timer_points": {
      "pending_points": 30.0,
      "ad_bonus_points": 10.0,
      "total_available_points": 40.0
    },
    "intermediate_points": {
      "total_claimed": 30.0,
      "claim_count": 3
    },
    "ended_at": "2025-12-11T12:52:00Z"
  }
}
```

### 5. 타이머 포인트 획득 (광고 시청)
**POST** `/api/sleep/claim-timer`

**Response:**
```json
{
  "success": true,
  "data": {
    "claimed_points": 40.0,
    "new_total_points": 1070,
    "remaining_pending": 0.0,
    "type": "timer_points"
  }
}
```

### 6. 일일 수면 현황 조회
**GET** `/api/sleep/daily-status`

**Response:**
```json
{
  "success": true,
  "data": {
    "date_key": "2025-12-11",
    "timer_points": {
      "pending_points": 30.0,
      "claimed_points": 140.0,
      "daily_limit": 200,
      "remaining_limit": 30.0
    },
    "intermediate_points": {
      "claimed_count": 3,
      "claimed_points": 30.0,
      "max_claims": 5,
      "remaining_claims": 2
    },
    "total_today_points": 200.0,
    "sleep_flow_completed": true,
    "current_session": {
      "session_id": 123,
      "status": "running",
      "elapsed_minutes": 60
    }
  }
}
```

### 7. 수면 세션 설정 업데이트
**PUT** `/api/sleep/update`

**Request Body:**
```json
{
  "mood": "tired",
  "memo": "피곤한 하루였어",
  "white_noise_type": "ocean",
  "white_noise_volume": 70
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": 123,
    "updated_fields": ["mood", "white_noise_type", "white_noise_volume"]
  }
}
```

## 🔄 프론트엔드 플로우

### 1. 수면 화면 UI 구성
```javascript
const SleepScreen = () => {
  return (
    <div>
      {/* 타이머 */}
      <Timer elapsed={elapsedMinutes} />
      
      {/* 타이머 포인트 영역 */}
      <div className="timer-points">
        <h3>수면 포인트: {timerPoints.pending}P</h3>
        <p>오늘 적립 가능: {timerPoints.remaining_limit}P</p>
      </div>
      
      {/* 중간 획득 포인트 버튼 */}
      <button 
        onClick={claimIntermediatePoints}
        disabled={intermediatePoints.remaining_claims === 0}
        className="intermediate-claim-btn"
      >
        🎁 포인트 받기 ({intermediatePoints.remaining_claims}/5)
      </button>
      
      {/* 수면 종료 버튼 */}
      <button onClick={endSleep} className="end-sleep-btn">
        수면 종료
      </button>
    </div>
  );
};
```

### 2. 중간 포인트 획득
```javascript
const claimIntermediatePoints = async () => {
  try {
    // 광고 재생
    await playAd();
    
    // 중간 포인트 획득
    const response = await fetch('/api/sleep/claim-intermediate', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.success) {
      showSuccessToast(`+${response.data.points_awarded}P 획득!`);
      updateIntermediatePoints(response.data);
      updateUserTotalPoints(response.data.new_total_points);
    }
  } catch (error) {
    if (error.code === 'INTERMEDIATE_LIMIT_REACHED') {
      showErrorToast('오늘 중간 포인트를 모두 받았어요!');
    }
  }
};
```

### 3. 수면 종료 팝업
```javascript
const showEndSleepPopup = (data) => {
  const popup = {
    title: "수면 완료!",
    content: `
      <div class="sleep-summary">
        <h3>수면 시간: ${data.total_minutes}분</h3>
        
        <div class="points-summary">
          <div class="timer-points">
            <h4>💤 수면 포인트</h4>
            <p>적립된 포인트: ${data.timer_points.pending_points}P</p>
            <p>광고 보너스: +${data.timer_points.ad_bonus_points}P</p>
            <p class="total">받을 수 있는 포인트: ${data.timer_points.total_available_points}P</p>
          </div>
          
          <div class="intermediate-points">
            <h4>🎁 중간 획득 포인트</h4>
            <p>이미 받은 포인트: ${data.intermediate_points.total_claimed}P</p>
            <p>획득 횟수: ${data.intermediate_points.claim_count}/5회</p>
          </div>
        </div>
      </div>
    `,
    buttons: [
      {
        text: "광고 보고 포인트 받기",
        action: () => claimTimerPoints()
      },
      {
        text: "포인트 없이 종료",
        action: () => closePopup()
      }
    ]
  };
  
  showPopup(popup);
};
```

### 4. 실시간 상태 업데이트
```javascript
const pollSleepStatus = async () => {
  const response = await fetch('/api/sleep/status', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  updateUI({
    timerPoints: response.data.timer_points,
    intermediatePoints: response.data.intermediate_points,
    elapsedTime: response.data.elapsed_minutes
  });
  
  // 중간 획득 버튼 활성화/비활성화
  updateIntermediateClaimButton(response.data.intermediate_points);
};

const updateIntermediateClaimButton = (intermediateData) => {
  const button = document.querySelector('.intermediate-claim-btn');
  
  if (intermediateData.remaining_claims > 0) {
    button.disabled = false;
    button.textContent = `🎁 포인트 받기 (${intermediateData.remaining_claims}/5)`;
  } else {
    button.disabled = true;
    button.textContent = '오늘 중간 포인트 완료 (5/5)';
  }
};
```

## ⚠️ 에러 처리

### 중간 포인트 관련 에러
```json
{
  "success": false,
  "error": {
    "code": "INTERMEDIATE_LIMIT_REACHED",
    "message": "오늘 중간 포인트 획득 한도에 도달했습니다."
  }
}
```

```json
{
  "success": false,
  "error": {
    "code": "NO_ACTIVE_SESSION",
    "message": "활성화된 수면 세션이 없습니다."
  }
}
```

## 🎯 핵심 포인트

### **포인트 시스템 분리**
1. **타이머 포인트**: 시간 기반, pending → 광고 → claimed
2. **중간 획득 포인트**: 즉시 지급, 최대 5회

### **일일 한도**
- 타이머 포인트: 최대 200P
- 중간 획득 포인트: 최대 50P (5회 × 10P)
- 총 최대: 250P/일

### **UI/UX 고려사항**
- 중간 획득 버튼은 눈에 띄게 배치
- 남은 횟수 실시간 표시
- 두 포인트 타입을 명확히 구분하여 표시
