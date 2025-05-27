// ✅ 1. 페이지 로드 시 초기 실행: 검색창 초기화, 자동완성 바인딩, 쿼리 파라미터로 자동검색 처리
window.onload = function () {
  const urlParams = new URLSearchParams(window.location.search);
  const q = urlParams.get('q');

  if (q) {
    document.getElementById('searchInput').value = q;
    searchMusic(); // URL에 쿼리 있으면 자동 검색 실행
  }

  hideSuggestions();

  // ✅ 검색창 입력 시: 검색어 없으면 추천어창 숨기기, 검색어 있으면 자동완성 로직 실행
  document.getElementById('searchInput').addEventListener('input', function () {
    const input = document.getElementById('searchInput');
    const suggestionsDiv = document.getElementById('suggestions');

    if (!input.value.trim()) {
      // 검색어 없으면 추천창 무조건 숨김
      hideSuggestions();
      return;
    }

    // 검색어 있으면 자동완성 로직 실행
    handleInputChange();
  });

  // ✅ Enter 키 입력 시 추천어창 무조건 숨기고 검색 실행
  document.getElementById('searchInput').addEventListener('keydown', function (event) {
    const suggestionsDiv = document.getElementById('suggestions');
    if (suggestionsDiv.style.display === 'block' && suggestionItems.length > 0) {
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        selectedSuggestionIndex = (selectedSuggestionIndex + 1) % suggestionItems.length;
        updateSuggestionActive();
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        selectedSuggestionIndex = (selectedSuggestionIndex - 1 + suggestionItems.length) % suggestionItems.length;
        updateSuggestionActive();
      } else if (event.key === 'Enter') {
        if (selectedSuggestionIndex >= 0 && suggestionItems[selectedSuggestionIndex]) {
          event.preventDefault();
          document.getElementById('searchInput').value = suggestionItems[selectedSuggestionIndex].textContent;
          hideSuggestions();
          searchMusic();
          return;
        }
      }
    }

    // 엔터 기본 동작 (자동완성창 없을 때도)
    if (event.key === 'Enter') {
      event.preventDefault();
      hideSuggestions();
      searchMusic();
    }
  });

  // ✅ 검색 버튼 클릭 시에도 추천어창 숨기고 검색 실행
  const searchButton = document.querySelector('.search-btn');
  if (searchButton) {
    searchButton.addEventListener('click', function () {
      hideSuggestions();
      searchMusic();
    });
  }
};

function updateSuggestionActive() {
  suggestionItems.forEach((item, idx) => {
    if (idx === selectedSuggestionIndex) {
      item.classList.add('active');
      item.scrollIntoView({ block: "nearest" });
    } else {
      item.classList.remove('active');
    }
  });
}

// ✅ 2. 검색창 입력 시 자동완성 API 요청 함수
function handleInputChange() {
  const input = document.getElementById('searchInput');
  const suggestionsDiv = document.getElementById('suggestions');

  if (!suggestionsDiv) return;

  const query = input.value.trim();
  if (!query) {
    hideSuggestions();
    return;
  }

  if (document.activeElement !== input) return; // 검색창이 포커스 상태일 때만 실행

  fetch(`/music/autocomplete/?q=${encodeURIComponent(query)}`)
    .then(response => response.json())
    .then(data => handleSuggestions(data))
    .catch(err => console.error("🔥 자동완성 요청 실패:", err));
}

// ✅ 3. 추천어 목록을 HTML로 표시하는 함수
function handleSuggestions(data) {
  const suggestionsDiv = document.getElementById('suggestions');
  if (!suggestionsDiv) return;

  suggestionsDiv.innerHTML = '';
  const suggestions = data.suggestions || [];

  if (suggestions.length === 0) {
    hideSuggestions();
    return;
  }

  suggestionItems = [];

  suggestions.forEach((suggestion, idx) => {
    const item = document.createElement('div');
    item.textContent = suggestion;
    item.classList.add('suggestion-item');
    item.onclick = () => {
      document.getElementById('searchInput').value = suggestion;
      hideSuggestions();
      searchMusic();
    };
    suggestionsDiv.appendChild(item);
    suggestionItems.push(item);
  });

  selectedSuggestionIndex = -1;
  suggestionsDiv.style.display = 'block';
}

let allResults = [];
let currentPage = 1;
const RESULTS_PER_PAGE = 5;

// ✅ 4. 검색 실행 함수 - 유튜브 API 호출 후 결과 렌더링
function searchMusic() {
  hideSuggestions();

  const query = document.getElementById('searchInput').value.trim();
  if (!query) return;

  hideSuggestions(); // 검색 시 자동완성 닫기

  fetch(`https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&q=${encodeURIComponent(query)}&videoCategoryId=10&maxResults=50&key=${API_KEY}`)
    .then(res => res.json())
    .then(data => {
      console.log("🔥 API 응답 결과:", data);
      if (!data.items || data.items.length === 0) {
        document.getElementById('results').innerHTML = '<p style="color:white;">검색 결과가 없습니다.</p>';
        document.getElementById('pagination').style.display = 'none';
        return;
      }

      allResults = data.items;
      currentPage = 1;
      renderResultsPage(currentPage);
      document.querySelector('.results-box').style.display = 'block';
      document.getElementById('pagination').style.display = 'block';
      document.getElementById('searchInput').value = '';

      hideSuggestions(); // ⭐️ 결과 나올 때도 무조건 닫기! (여기 추가!)
    })
    .catch(err => {
      console.error("🔥 유튜브 검색 실패:", err);
      document.getElementById('searchInput').value = '';

      hideSuggestions(); // ⭐️ 결과 나올 때도 무조건 닫기! (여기 추가!)
    });
}

// ✅ 🔥 페이지별 결과 렌더링
function renderResultsPage(page) {
  const results = document.getElementById('results');
  results.innerHTML = "";

  const start = (page - 1) * RESULTS_PER_PAGE;
  const end = start + RESULTS_PER_PAGE;
  const paginatedItems = allResults.slice(start, end);

  paginatedItems.forEach(item => {
    const videoId = item.id.videoId;
    const title = item.snippet.title;
    const thumbnail = item.snippet.thumbnails.medium.url;

    results.innerHTML += `
      <div class="video">
        <img src="${thumbnail}" alt="${title}" onclick="openPanel('${videoId}', \`${title}\`)">
        <p title="${title}">${title}</p>
      </div>
    `;
  });

  renderPagination();
}

// ✅ 🔥 페이지네이션 바 렌더링
function renderPagination() {
  const pagination = document.getElementById('pagination');
  if (!pagination) return;

  pagination.innerHTML = "";

  const pageCount = Math.ceil(allResults.length / RESULTS_PER_PAGE);

  for (let i = 1; i <= pageCount; i++) {
    const btn = document.createElement('button');
    btn.textContent = i;
    btn.classList.add('page-btn');
    if (i === currentPage) btn.classList.add('active');

    btn.addEventListener('click', () => {
      currentPage = i;
      renderResultsPage(currentPage);
    });

    pagination.appendChild(btn);
  }
}

// ✅ 5. 썸네일 클릭 시 AI로 곡 제목 분석 후 상세 페이지 이동
function openPanel(videoId, originalTitle) {
  analyzeTitleWithAI(originalTitle).then(({ artist, title }) => {
    if (artist && title) {
      const url = `/music/lyrics-info/?artist=${encodeURIComponent(artist)}&title=${encodeURIComponent(title)}&videoId=${encodeURIComponent(videoId)}`;
      window.location.href = url;
    } else {
      alert('AI로 가수/곡명을 추출하지 못했습니다.');
    }
  });
}

// ✅ 6. 영상 제목을 GPT에게 보내서 artist/title 추출하는 함수
function analyzeTitleWithAI(title) {
  return fetch('/music/analyze-title/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title })
  })
    .then(res => res.json())
    .catch(err => {
      console.error("🔥 AI 분석 실패:", err);
      return { artist: null, title: null };
    });
}

// ✅ 7. 추천어창 숨기는 유틸 함수
function hideSuggestions() {
  const suggestions = document.getElementById('suggestions');
  if (suggestions) {
    suggestions.style.display = 'none';
    suggestions.innerHTML = '';
  }
}

// ✅ 8. 음성 인식 기능 (마이크 버튼 클릭 시 검색어 받아오기)
let recognition = null;
let isManuallyStopped = false;

const micBtn = document.getElementById('micBtn');
const stopBtn = document.getElementById('stopBtn');
const searchInput = document.getElementById('searchInput');

micBtn.addEventListener('click', () => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("이 브라우저는 음성 인식을 지원하지 않습니다.");
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = 'ko-KR';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.start();
  micBtn.style.display = "none";
  stopBtn.style.display = "inline";

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    searchInput.value = transcript;
    stopMicRecognitionUI();
  };

  recognition.onerror = (event) => {
    if (!isManuallyStopped) {
      alert("음성 인식 오류: " + event.error);
    }
    stopMicRecognitionUI();
  };

  recognition.onend = () => {
    stopMicRecognitionUI();
    isManuallyStopped = false;
  };
});

stopBtn.addEventListener('click', () => {
  if (recognition) {
    isManuallyStopped = true;
    recognition.stop();
  }
  stopMicRecognitionUI();
});

function stopMicRecognitionUI() {
  micBtn.style.display = "inline";
  stopBtn.style.display = "none";
}

// 자동완성창 닫기용 바디 클릭 리스너
document.addEventListener('click', function (e) {
  const searchInput = document.getElementById('searchInput');
  const suggestionsDiv = document.getElementById('suggestions');
  // 두 영역이 없으면 아무것도 하지 않음
  if (!suggestionsDiv || !searchInput) return;

  // e.target이 검색창, 추천창, 추천창의 자식이 아니면 닫기
  if (
    !searchInput.contains(e.target) &&      // 검색창 클릭 X
    !suggestionsDiv.contains(e.target)      // 추천창 클릭 X
  ) {
    hideSuggestions();
  }
});
