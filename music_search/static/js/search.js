let allResults = [];
let currentPage = 1;
const RESULTS_PER_PAGE = 5;

// ✅ 페이지 로드 시
window.onload = function () {
  const urlParams = new URLSearchParams(window.location.search);
  const q = urlParams.get('q');

  if (q) {
    document.getElementById('searchInput').value = q;
    searchMusic();
  }

  // ✅ 검색 버튼 클릭
  const searchButton = document.querySelector('.search-btn');
  if (searchButton) {
    searchButton.addEventListener('click', function () {
      searchMusic();
      document.getElementById('searchInput').value = '';
    });
  }

  // ✅ 엔터 입력 시 검색 실행
  const searchInput = document.getElementById('searchInput');
  searchInput.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      searchMusic();
      searchInput.value = '';
    }
  });
};

// 🔥 검색 실행 함수
function searchMusic() {
  const inputEl = document.getElementById('searchInput');
  const query = inputEl.value.trim();
  if (!query) return;

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
