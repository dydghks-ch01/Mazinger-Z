let allResults = [];
let currentPage = 1;
const RESULTS_PER_PAGE = 5;
// ✅ 디바운스 함수 추가
let debounceTimer;
let autocompleteController;  // 🔥 컨트롤러 변수 추가

window.onload = function () {
  const urlParams = new URLSearchParams(window.location.search);
  const q = urlParams.get('q');

  if (q) {
    document.getElementById('searchInput').value = q;
    searchMusic();
  }

  const searchInput = document.getElementById('searchInput');
  const suggestionsDiv = document.getElementById('suggestions');
  const searchButton = document.querySelector('.search-btn');  // 🔥 여기 위치!

  // ✅ input 이벤트: 입력 없으면 추천어 숨기기, 있으면 debounce로 요청
  searchInput.addEventListener('input', () => {
    if (!searchInput.value.trim()) {
      hideSuggestions();
    } else {
      debouncedInputChange();
    }
  });

  // ✅ focus 이벤트: 입력 없으면 추천어 숨김
  searchInput.addEventListener('focus', () => {
    if (!searchInput.value.trim()) {
      hideSuggestions();
    }
  });

  // ✅ 검색 버튼 클릭
  if (searchButton) {
    searchButton.addEventListener('click', function () {
      if (autocompleteController) autocompleteController.abort();
      clearTimeout(debounceTimer);
      hideSuggestions();
      searchMusic();
      searchInput.value = '';
    });
  }

  // ✅ 엔터 입력 시 검색
  searchInput.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      if (autocompleteController) autocompleteController.abort();
      clearTimeout(debounceTimer);
      hideSuggestions();
      searchMusic();
      searchInput.value = '';
    }
  });
};



// 🔥 검색 실행 함수
// 🔥 검색 실행 함수
function searchMusic() {
  const inputEl = document.getElementById('searchInput');
  const query = inputEl.value.trim();
  if (!query) return;

  // 🔥 자동완성 숨김 처리
  hideSuggestions();

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
    })
    .catch(err => {
      console.error("🔥 유튜브 검색 실패:", err);
    });
}

// // 🔥 검색창 focus 시 자동완성 복구
// document.getElementById('searchInput').addEventListener('focus', function () {
//   handleInputChange(this, document.getElementById('suggestions'));
// });


// 🔥 페이지별 결과 렌더링
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

// 🔥 페이지네이션
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

// 🔥 AI 분석
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


// ✅ 자동완성 숨김 처리
function hideSuggestions() {
  const suggestions = document.getElementById('suggestions');
  if (suggestions) {
    suggestions.style.display = 'none';
    suggestions.innerHTML = '';
  }
}

// ✅ 입력 시 추천어 처리
function handleInputChange(input, suggestionsDiv) {
  if (!suggestionsDiv) return;

  if (!input.value.trim()) {
    suggestionsDiv.style.display = 'none';
    suggestionsDiv.innerHTML = '';
    return;
  }

  if (document.activeElement !== input) return;

  // 🔥 이전 autocomplete 요청이 있으면 취소
  if (autocompleteController) {
    autocompleteController.abort();
  }

  // 🔥 새로운 AbortController 생성
  autocompleteController = new AbortController();
  const signal = autocompleteController.signal;

  const query = input.value;
  fetch(`/music/autocomplete/?q=${encodeURIComponent(query)}`, { signal })
    .then(res => res.json())
    .then(data => handleSuggestions(data, suggestionsDiv, input))
    .catch(err => {
      if (err.name === 'AbortError') {
        console.log("🔥 자동완성 요청 취소됨");
      } else {
        console.error("🔥 자동완성 요청 실패:", err);
      }
    });
}

function handleSuggestions(data, suggestionsDiv, input) {
  if (!suggestionsDiv) return;

  suggestionsDiv.innerHTML = '';
  const suggestions = data.suggestions || [];

  if (suggestions.length === 0) {
    suggestionsDiv.style.display = 'none';
    return;
  }

  suggestions.forEach(suggestion => {
    const item = document.createElement('div');
    item.textContent = suggestion;
    item.onclick = () => {
      input.value = suggestion;
      suggestionsDiv.innerHTML = '';
      suggestionsDiv.style.display = 'none';
    };
    suggestionsDiv.appendChild(item);
  });

  suggestionsDiv.style.display = 'block';
}



function debounce(func, delay) {
  return function (...args) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => func.apply(this, args), delay);
  };
}

// ✅ 검색창 입력 시 자동완성 요청
const searchInput = document.getElementById('searchInput');
const suggestionsDiv = document.getElementById('suggestions');

const debouncedInputChange = debounce(() => {
  handleInputChange(searchInput, suggestionsDiv);
}, 100);

searchInput.addEventListener('input', debouncedInputChange);

