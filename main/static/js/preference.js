// ✅ 질문 목록 정의
const questions = [
  "친구들이랑 모이면 내가 분위기를 주도하는 편이다.",
  "주말에는 야외 활동이나 운동을 즐긴다.",
  "영화나 드라마를 보면 쉽게 감정이입한다.",
  "최신 유행이나 신상 아이템을 궁금해하는 편이다.",
  "혼자 카페나 방에서 조용히 쉬는 걸 좋아한다.",
  "나는 즉흥적으로 계획을 바꾸는 걸 즐긴다.",
  "오래된 물건이나 빈티지 감성을 좋아한다."
];

let current = 0;
let answers = Array(questions.length).fill(null);
let selectedSido = null;
let selectedGugun = null;

// ✅ 시/도 초기 옵션 추가
function populateSidoOptions() {
  const sidoSelect = document.getElementById("sido-select");
  const sidoList = [
    "서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시",
    "대전광역시", "울산광역시", "세종특별자치시", "경기도", "강원특별자치도",
    "충청북도", "충청남도", "전라북도", "전라남도", "경상북도", "경상남도", "제주특별자치도"
  ];

  sidoList.forEach(sido => {
    const option = document.createElement("option");
    option.value = sido;
    option.textContent = sido;
    sidoSelect.appendChild(option);
  });
}

// ✅ 색상 클래스 매핑
function getButtonClass(idx) {
  return ["strong-disagree", "disagree", "neutral", "agree", "strong-agree"][idx];
}

// ✅ 질문 로딩 및 버튼 렌더링
function loadQuestion() {
  const qBox = document.getElementById("question-box");
  if (!qBox) return;

  if (current >= questions.length) {
    qBox.style.display = "none";
    document.getElementById("region-question").style.display = "block";
    updateResultButtonState();
    return;
  }

  const labels = ["매우 아니다", "약간 아니다", "모르겠다", "약간 그렇다", "매우 그렇다"];
  qBox.innerHTML = `
    <div class="question">Q${current + 1}. ${questions[current]}</div>
    <div class="answer-buttons">
      ${labels.map((label, idx) => `
        <button class="answer-btn svg-border-button ${getButtonClass(idx)}" onclick="selectAnswer(${idx + 1}, this)">${label}<svg viewBox="0 0 100 40" preserveAspectRatio="none">
          <rect x="0" y="0" width="100" height="40" />
        </svg></button>
      `).join("")}
    </div>
    <div class="nav-buttons">
      <button id="prev-btn" onclick="prevQuestion()">이전</button>
      <button id="next-btn" onclick="loadQuestion()">다음</button>
    </div>
  `;

  // ✅ 버튼 제어는 반드시 렌더링 이후에!
  setTimeout(() => {
    const prevBtn = document.getElementById("prev-btn");
    const nextBtn = document.getElementById("next-btn");

    if (prevBtn) prevBtn.disabled = current === 0;
    if (nextBtn) nextBtn.style.display = current < questions.length - 1 ? "inline-block" : "none";

    if (answers[current] !== null) {
      const selected = document.querySelectorAll(".answer-buttons button")[answers[current] - 1];
      if (selected) selected.classList.add("selected");
    }
  }, 0);
}

// ✅ 답변 선택 시 다음 질문
function selectAnswer(value, btn) {
  answers[current] = value;
  document.querySelectorAll(".answer-buttons button").forEach(b => b.classList.remove("selected"));
  btn.classList.add("selected");

  setTimeout(() => {
    current++;
    loadQuestion();
    updateProgress();
    updateResultButtonState();
  }, 300);
}

// ✅ 이전 질문으로 이동
function prevQuestion() {
  if (current > 0) {
    current--;
    loadQuestion();
    updateProgress();
    updateResultButtonState();
  }
}

// ✅ 진행 바 업데이트
function updateProgress() {
  const percent = (current / questions.length) * 100;
  document.getElementById("progress").style.width = `${percent}%`;
}

// ✅ 시/도 선택 시 구군 로딩
function onSidoSelect(sido) {
  selectedSido = sido;
  selectedGugun = null;

  const gugunSelect = document.getElementById("gugun-select");
  gugunSelect.innerHTML = '<option value="">구/군을 선택하세요</option>';
  gugunSelect.disabled = true;

  fetch(`/get_guguns/?sido=${encodeURIComponent(sido)}`)
    .then(res => res.json())
    .then(data => {
      data.guguns.forEach(gugun => {
        const option = document.createElement("option");
        option.value = gugun;
        option.textContent = gugun;
        gugunSelect.appendChild(option);
      });
      gugunSelect.disabled = false;
      updateResultButtonState();
    });
}

// ✅ 구군 선택 처리
function onGugunSelect(gugun) {
  selectedGugun = gugun;
  updateResultButtonState();
}

// ✅ 결과 버튼 활성화 조건 체크
function updateResultButtonState() {
  const resultBtn = document.getElementById("result-btn");
  const regionReady = selectedSido && selectedGugun;
  const allAnswered = answers.every(ans => ans !== null);
  const canClick = regionReady && allAnswered;

  if (resultBtn) {
    resultBtn.disabled = !canClick;
    if (canClick) {
      resultBtn.classList.add("active");
    } else {
      resultBtn.classList.remove("active");
    }
  }
}

// ✅ 결과 계산 및 추천 요청
function calculateResult() {
  if (!selectedSido || !selectedGugun) return;

  fetch(`/get_weather_genre/?sido=${encodeURIComponent(selectedSido)}&gugun=${encodeURIComponent(selectedGugun)}`)
    .then(res => res.json())
    .then(data => {
      const pty = data.pty || "0";
      const weatherBonus = weatherScoreMap[pty] || {};
      const [bright, fast, emotion, trendy, calm, indie, classic] = answers;

      const final = {
        bright: (bright || 0) + (weatherBonus.bright || 0),
        fast: (fast || 0) + (weatherBonus.fast || 0),
        emotion: (emotion || 0) + (weatherBonus.emotion || 0),
        trendy: (trendy || 0) + (weatherBonus.trendy || 0),
        calm: (calm || 0) + (weatherBonus.calm || 0),
        indie: (indie || 0) + (weatherBonus.indie || 0),
        classic: (classic || 0) + (weatherBonus.classic || 0)
      };

      let genre = "팝";
      if (final.bright >= 4 && final.fast >= 4 && final.emotion >= 4) genre = "K-pop, EDM";
      else if (final.calm >= 4 && final.emotion >= 4) genre = "발라드";
      else if (final.fast >= 4 && final.trendy >= 4) genre = "힙합, 일렉트로닉";
      else genre = "OST, R&B";

      document.getElementById("result").innerText = `추천 장르: ${genre}`;
      fetch(`/recommend_by_genre/?genre=${encodeURIComponent(genre)}`)
        .then(res => res.json())
        .then(data => {
          const recDiv = document.getElementById("recommend-songs");
          recDiv.innerHTML = "<div class='recommend-title'>추천 음악</div>";
          data.songs.forEach(song => {
            const div = document.createElement("div");
            div.className = "recommended-song";
            div.innerText = `${song.title} - ${song.artist} (${song.normalized_genre})`;
            recDiv.appendChild(div);
          });
        });
    });
}

function restartPreference() {
  current = 0;
  answers = Array(questions.length).fill(null);
  selectedSido = null;
  selectedGugun = null;

  document.getElementById("sido-select").selectedIndex = 0;
  document.getElementById("gugun-select").innerHTML = '<option value="">구/군을 선택하세요</option>';
  document.getElementById("gugun-select").disabled = true;

  document.getElementById("question-box").style.display = "flex";
  document.getElementById("region-question").style.display = "none";
  document.getElementById("result").innerText = "";
  document.getElementById("recommend-songs").innerHTML = "";

  updateProgress();
  updateResultButtonState();
  loadQuestion();
}


// ✅ 초기 실행 함수
function initPreferenceTest() {
  populateSidoOptions(); // ✅ 시/도 목록 초기화
  current = 0;
  answers = Array(questions.length).fill(null);
  selectedSido = null;
  selectedGugun = null;

  document.getElementById("question-box").style.display = "flex";
  document.getElementById("region-question").style.display = "none";
  document.getElementById("result").innerText = "";
  document.getElementById("recommend-songs").innerHTML = "";

  loadQuestion();
  updateProgress();
  updateResultButtonState();
}

// ✅ DOM 로딩 후 실행
document.addEventListener("DOMContentLoaded", initPreferenceTest);