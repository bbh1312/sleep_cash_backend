# 📱 앱 재시작 및 수면 세션 복원 지침서

## 🎯 개요
사용자가 수면 세션 중 앱을 종료하고 다시 실행할 때, 기존 세션을 자동으로 복원하는 방법입니다.

## 🔄 앱 시작 시 플로우

### 1. 앱 실행 시 첫 번째 API 호출
```javascript
const initializeApp = async () => {
  try {
    const response = await fetch('/api/sleep/daily-status', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const data = response.data;
    
    if (data.current_session) {
      // 활성 세션 있음 → 수면 화면으로 복원
      resumeSleepSession(data);
    } else {
      // 활성 세션 없음 → 일반 플로우
      checkSleepFlowStatus(data);
    }
  } catch (error) {
    console.error('앱 초기화 실패:', error);
  }
};
```

### 2. 세션 복원 함수
```javascript
const resumeSleepSession = (dailyStatus) => {
  const session = dailyStatus.current_session;
  
  // 수면 화면으로 네비게이션
  navigation.navigate('SleepScreen', {
    sessionId: session.session_id,
    isResuming: true,
    initialData: {
      elapsedMinutes: session.elapsed_minutes,
      timerPoints: dailyStatus.timer_points,
      intermediatePoints: dailyStatus.intermediate_points,
      totalTodayPoints: dailyStatus.total_today_points
    }
  });
};
```

### 3. 수면 화면 복원 로직
```javascript
const SleepScreen = ({ route }) => {
  const { sessionId, isResuming, initialData } = route.params || {};
  
  useEffect(() => {
    if (isResuming && initialData) {
      // 기존 세션 복원
      restoreSessionState(initialData);
    } else {
      // 새 세션 시작
      startNewSession();
    }
  }, []);
  
  const restoreSessionState = (data) => {
    // 1. 타이머 상태 복원
    setElapsedMinutes(data.elapsedMinutes);
    
    // 2. 포인트 상태 복원
    setTimerPoints(data.timerPoints);
    setIntermediatePoints(data.intermediatePoints);
    
    // 3. UI 상태 업데이트
    updateIntermediateButton(data.intermediatePoints.remaining_claims);
    
    // 4. 실시간 폴링 시작
    startStatusPolling();
    
    // 5. 타이머 재시작 (경과 시간부터)
    startTimerFromElapsed(data.elapsedMinutes);
  };
};
```

## 📊 API 응답 데이터 구조

### `/api/sleep/daily-status` 응답
```json
{
  "success": true,
  "data": {
    "current_session": {
      "session_id": 12,
      "status": "running",
      "elapsed_minutes": 15
    },
    "timer_points": {
      "pending_points": 7.5,
      "claimed_points": 0.0,
      "remaining_limit": 192.5
    },
    "intermediate_points": {
      "claimed_count": 2,
      "remaining_claims": 3,
      "claimed_points": 20.0
    },
    "total_today_points": 27.5,
    "sleep_flow_completed": true
  }
}
```

### 세션이 없을 때 응답
```json
{
  "success": true,
  "data": {
    "current_session": null,
    "timer_points": {
      "pending_points": 0.0,
      "claimed_points": 50.0,
      "remaining_limit": 150.0
    },
    "intermediate_points": {
      "claimed_count": 3,
      "remaining_claims": 2,
      "claimed_points": 30.0
    },
    "sleep_flow_completed": true
  }
}
```

## 🎮 상태별 처리 로직

### Case 1: 활성 세션 있음
```javascript
if (data.current_session) {
  // 수면 화면으로 바로 이동
  // 타이머, 포인트 상태 복원
  // 실시간 폴링 재시작
}
```

### Case 2: 활성 세션 없음 + 플로우 완료
```javascript
if (!data.current_session && data.sleep_flow_completed) {
  // 홈 화면 표시
  // "수면 시작" 버튼 → 바로 수면 화면
}
```

### Case 3: 활성 세션 없음 + 플로우 미완료
```javascript
if (!data.current_session && !data.sleep_flow_completed) {
  // 수면 플로우 시작
  // 광고 팝업 → 기분 선택 → 백색소음 선택
}
```

## ⏱️ 타이머 복원 로직

### 1. 경과 시간 기반 타이머 시작
```javascript
const startTimerFromElapsed = (elapsedMinutes) => {
  // 현재 분의 초 계산 (0~59초 사이에서 시작)
  const currentSecond = (elapsedMinutes * 60) % 60;
  const startSecond = currentSecond === 0 ? 59 : (59 - currentSecond);
  
  setTimerSeconds(startSecond);
  
  // 1초마다 감소
  const interval = setInterval(() => {
    setTimerSeconds(prev => {
      if (prev <= 0) {
        // 1분 완료 → 포인트 증가 애니메이션
        showPointIncrement(0.5);
        return 59;
      }
      return prev - 1;
    });
  }, 1000);
  
  return interval;
};
```

### 2. 실시간 동기화
```javascript
const syncWithServer = async () => {
  const response = await fetch('/api/sleep/status');
  const serverData = response.data;
  
  // 서버 데이터로 UI 업데이트
  setTimerPoints(serverData.timer_points);
  setIntermediatePoints(serverData.intermediate_points);
  
  // 경과 시간 차이가 클 경우 조정
  if (Math.abs(serverData.elapsed_minutes - localElapsedMinutes) > 1) {
    setElapsedMinutes(serverData.elapsed_minutes);
  }
};

// 30초마다 서버와 동기화
setInterval(syncWithServer, 30000);
```

## 🔄 중간 획득 버튼 상태 복원

### 버튼 상태 업데이트
```javascript
const updateIntermediateButton = (remainingClaims) => {
  const button = document.querySelector('.intermediate-claim-btn');
  
  if (remainingClaims > 0) {
    button.disabled = false;
    button.textContent = `🎁 포인트 받기 (${remainingClaims}/5)`;
    button.className = 'intermediate-claim-btn active';
  } else {
    button.disabled = true;
    button.textContent = '오늘 중간 포인트 완료 (5/5)';
    button.className = 'intermediate-claim-btn disabled';
  }
};
```

## 🚨 에러 처리

### 네트워크 오류 시
```javascript
const handleNetworkError = () => {
  // 로컬 상태 유지
  // 재연결 시 서버와 동기화
  showToast('네트워크 연결을 확인해주세요');
  
  // 5초마다 재시도
  setTimeout(initializeApp, 5000);
};
```

### 토큰 만료 시
```javascript
const handleTokenExpired = () => {
  // 로그인 화면으로 이동
  navigation.navigate('Login');
  showToast('다시 로그인해주세요');
};
```

## 📱 사용자 경험 고려사항

### 1. 로딩 상태 표시
```javascript
const [isRestoring, setIsRestoring] = useState(true);

// 복원 중 스플래시 화면 표시
if (isRestoring) {
  return <SplashScreen message="수면 상태를 복원하는 중..." />;
}
```

### 2. 복원 완료 알림
```javascript
const showRestorationComplete = (elapsedMinutes) => {
  showToast(`수면이 계속되고 있어요 (${elapsedMinutes}분 경과)`);
};
```

### 3. 데이터 불일치 처리
```javascript
const handleDataMismatch = () => {
  // 서버 데이터를 우선으로 UI 업데이트
  // 사용자에게 상태 동기화 완료 알림
  showToast('수면 상태가 동기화되었어요');
};
```

## 🎯 핵심 포인트

1. **앱 시작 시 반드시 `/api/sleep/daily-status` 호출**
2. **`current_session`이 있으면 무조건 수면 화면으로 복원**
3. **서버 데이터를 기준으로 모든 상태 복원**
4. **타이머는 경과 시간부터 재시작**
5. **30초마다 서버와 동기화**
6. **네트워크 오류 시 로컬 상태 유지 후 재연결 시 동기화**

이 지침서를 따르면 사용자가 언제든 앱을 재시작해도 수면 세션이 끊김없이 이어집니다.
