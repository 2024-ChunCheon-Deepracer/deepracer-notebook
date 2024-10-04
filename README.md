# deepracer-notebook
2024 춘천 AWS 딥레이서 챔피언십



## Overview
Section 1: 첫 번째 모델 트레이닝
Section 2: AWS DeepRacer League 가상콘솔에서 Evaluation
Section 3: 모델 트레이닝 및 모델 개선
Section 4: 대회 제출

### Section 1: 첫 번째 모델 트레이닝
계정 정보를 이용하여 AWS Console 에 로그인 합니다.
리전(Region)이 North Virginia 인지 확인하고 AWS DeepRacer(https://console.aws.amazon.com/deepracer/home?region=us-east-1)로 이동합니다.
AWS DeepRacer 페이지에서, 왼쪽 메뉴의 Reinforcement learning를 선택합니다.

Reinforcement learning 메뉴를 선택하면 모델 페이지가 나타나고 모델의 상태(status)를 확인할 수 있습니다. 모델 생성 뿐만 아니라, 모델 다운로드, 복제, 삭제도 할 수 있습니다.
 Create model 버튼을 클릭해서 모델을 만들 수 있습니다. 모델을 생성한 후에는 이 페이지를 통해 학습 중(Training), 완료(Ready) 등 모델의 상태(status)를 확인할 수 있습니다. 
 모델의 상태(status)가 "완료(Ready)"이면 모델 트레이닝이 완료되었음을 의미하는 것으로, 모델을 다운로드 하거나 테스트(evaluate)할 수 있습니다. 
<img width="1512" alt="스크린샷 2024-10-04 오후 10 50 05" src="https://github.com/user-attachments/assets/eabc3b48-c385-41a4-9ac7-887738df1b2f">


#### Action Space
학습 과정 및 실 주행에서 선택 할 수 있는 action space를 정의합니다. Action은 자동차가 취할 수 있는 스피드와 조향각의 조합입니다. AWS DeepRacer의 더 세밀한 주행을 위해 continuous action space가 아닌 discrete acation space를 사용합니다. 
최대 속도(maximum speed), 속도 레벨(speed levels), 최대 조향 각도(maximum steering angle), 그리고 조향 레벨 (steering levels) 을 지정하게 됩니다.
<img width="1512" alt="스크린샷 2024-10-04 오후 10 48 08" src="https://github.com/user-attachments/assets/6ce7cb9b-13b0-4442-9ff0-4194d7dc9e8f">

최대 조향 각도는 차량의 앞 바퀴가 왼쪽과 오른쪽으로 회전 할 수있는 최대 각도입니다. 바퀴가 얼마나 크게 회전 할 수 있는지에 대한 한계가 있으며, 최대 회전 각도는 30도입니다.
조향 레벨은 양쪽 최대 조향 각도 사이가 몇 단계인지를 나타냅니다. 따라서 최대 조향 각도가 30도인 경우 + 30도가 왼쪽이고 -30도가 오른쪽입니다. 조향 레벨이 5인 경우 왼쪽에서 오른쪽 방향으로 30도, 15도, 0도, -15도 및 -30 도의 조향 각도가 동작 공간에 표시됩니다. 조향 각도은 언제나 0도를 기준으로 대칭입니다.
최대 속도는 자동차가 시뮬레이터에서 운전할 최대 속도를 m/s로 측정 한 것입니다.
속도 레벨은 최대 속도(포함)에서 0까지의 속도 레벨의 개수를 나타냅니다. 만약 최대 속도가 3m/s이고 속도 레벨이 3이라면, action space에는 1m/s, 2m/s, 3m/s의 속도가 포함됩니다. 간단히 3m/s 를 3으로 나누면 1m/s가 되고, 0m/s 에서 3m/s로 1m/s씩 증가합니다. 0m/s는 action space에 포함되지 않습니다.( action space가 많을스록 학습이 더 오래 걸릴 수 있습니다.)

#### 최적 코스 추출
<img width="649" alt="스크린샷 2024-10-04 오후 11 03 48" src="https://github.com/user-attachments/assets/6eb2361e-ef9a-42e0-80aa-4d0c1dbf3d69">

#### Reward function
강화 학습에서는 보상 함수(reward function)를 잘 설계하는 것이 매우 중요합니다. 보상 함수는 학습된 RL 모델이 자율 주행을 할 때 우리가 원하는 대로 행동 할 수 있도록 합니다.
 실제로 학습이 수행되는 동안 매번 행동을 취한 후 보상이 계산되며, 시뮬레이터가 제공하는 다양한 변수들을 사용해서 보상 함수 로직을 만들 수 있습니다. Python 언어로 자동차의 조향각도, 속도, (x,y) 좌표같은 레이스 트랙과 자동차의 관계, waypoint와 같은 레이스 트랙 값들을 활용한 보상 함수를 만들 수 있습니다.

### 하이퍼파라미터
학습 알고리즘에서 사용할 하이퍼 파라미터를 지정합니다. 하이퍼 파라미터는 학습 성과를 향상시키는 데 사용됩니다.
**스텝(step)**은 경험이라고도 하며 (s,a,r,s’) 의 튜플입니다. 여기서 s는 카메라에 의해 캡처된 관찰 (또는 상태(state)), 차량이 취한 행동(action)은 a, 이 행동으로 인해 발생한 예상된 보상(reward)은 r, 그리고 조치를 취한 후 새로운 관찰 (또는 새로운 상태(new state)) 은 s'입니다.
**경험 버퍼(experience buffer)**는 학습 중 정해진 수의 에피소드로 부터 수집된 정렬된 스텝들로 구성됩니다.
배치는 일정 기간 동안 시뮬레이션에서 얻은 경험의 일부를 나타내는 순서가 있는 경험(스텝) 목록입니다. 이는 정책 네트워크 가중치를 업데이트하는 데 사용됩니다.
경험 버퍼에서 무작위로 샘플링된 배치 집합을 학습 데이터셋 이라고 하며 정책 네트워크(policy network) 가중치를 학습시키는데 사용됩니다.


### Section 2: AWS DeepRacer League 가상콘솔에서 Evaluation
<img width="628" alt="스크린샷 2024-10-04 오후 11 02 10" src="https://github.com/user-attachments/assets/09a03631-2807-4f5a-b31f-74eeface8de0">

### Section 3: 모델 트레이닝 및 모델 개선

### 주행로그 분석
<img width="402" alt="스크린샷 2024-10-04 오후 11 11 23" src="https://github.com/user-attachments/assets/bb1105ee-34c9-4764-bc95-a20c624674d1">
<img width="637" alt="스크린샷 2024-10-04 오후 11 11 54" src="https://github.com/user-attachments/assets/ddab661d-1f5b-46f0-a872-43115670089d">



### 보상함수 튜닝
모델 평가를 바탕으로 모델이 트랙을 안정적으로 완주할 수 있는지 여부와 평균 랩타임이 어느 정도인지 알게 됩니다. 보상 함수와 하이퍼 파라미터를 반복적으로 실험하여 여러 가지 주행 특성을 반영한 몇 가지 보상 함수를 시험해본 후, 시뮬레이터에서 평가해 가장 성능이 좋은 함수를 선택합니다.
기존 학습 모델을 Clone 하여 더 빠른 주행에 가산점을 주도록 보상 함수를 수정합니다. 저희 팀은 더 빠른 랩타임을 얻기 위해, max_speed 최대 속도를 늘리면서 보상함수를 튜닝해주었습니다. 


### Section 4: 대회 제출

<img width="600" alt="스크린샷 2024-10-04 오후 11 02 48" src="https://github.com/user-attachments/assets/31015c32-7374-4753-b6f4-7d8d043f1a47">




### 예선

### 본선

### 결선
