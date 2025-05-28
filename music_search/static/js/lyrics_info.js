// ✅ 추천어 번역 로직도 통합
const translatedLyrics = {
  original: "",
  ko: "",
  en: "",
  ja: "",
  zh: ""
};

window.onload = function () {
  const urlParams = new URLSearchParams(window.location.search);
  const artist = urlParams.get('artist');
  const title = urlParams.get('title');
  const videoId = urlParams.get('videoId');

  // ✅ 유튜브 영상 iframe
  const youtubePlayer = document.getElementById('youtubePlayer');
  youtubePlayer.style.display = 'block';
  if (videoId && videoId !== 'no-video') {
    setTimeout(() => {
      youtubePlayer.src = `https://www.youtube.com/embed/${videoId}?autoplay=1`;
    }, 10);
    document.getElementById("youtubePlayer").addEventListener("load", () => {
      const loader = document.getElementById("youtubeLoading");
      if (loader) loader.style.display = "none";
    });
  } else {
    youtubePlayer.src = '';
    youtubePlayer.style.display = 'none';
  }

  // ✅ Apple Music 정보 로딩
  if (artist && title) {
    setTimeout(() => {
      fetchTrackFromApple(`${artist} ${title}`);
    }, 20);
  }

  // ✅ 가사 및 태그 분석
  if (artist && title) {
    setTimeout(() => {
      fetchLyricsTranslateAndTag(artist, title);
    }, 500);
  }

  // ✅ 검색 버튼 클릭 (자동완성 제거)
  const searchButton = document.querySelector('.search-btn');
  if (searchButton) {
    searchButton.addEventListener('click', function () {
      redirectSearch();
    });
  }

  // ✅ 엔터 입력 시 검색 실행 (자동완성 제거)
  const searchInput = document.getElementById('searchInput');
  searchInput.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      redirectSearch();
    }
  });
}

// ✅ 가사 및 태그 분석
async function fetchLyricsTranslateAndTag(artist, title) {
  const lyricsContent = document.getElementById('lyricsContent');

  try {
    const res = await fetch('/music/lyrics/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ artist, title })
    });
    const data = await res.json();
    if (!data.lyrics) {
      lyricsContent.innerHTML = "❌ Unable to load lyrics.";
      return;
    }

    translatedLyrics.original = data.lyrics.replace(/(\r\n|\r|\n)/g, '<br>');
    translatedLyrics.ko = data.ko_lyrics ? data.ko_lyrics.replace(/(\r\n|\r|\n)/g, '<br>') : '';
    translatedLyrics.en = data.en_lyrics ? data.en_lyrics.replace(/(\r\n|\r|\n)/g, '<br>') : '';
    translatedLyrics.ja = data.ja_lyrics ? data.ja_lyrics.replace(/(\r\n|\r|\n)/g, '<br>') : '';
    translatedLyrics.zh = data.zh_lyrics ? data.zh_lyrics.replace(/(\r\n|\r|\n)/g, '<br>') : '';

    lyricsContent.innerHTML = translatedLyrics.original || "⚠️ Unable to load lyrics.";

    await fetch('/music/save-tagged-song/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, artist, lyrics: data.lyrics })
    })
      .then(res => res.json())
      .then(response => {
        if (response.status === 'success') {
          console.log("✅ 태그 저장 완료:", response.tags);
        } else {
          console.warn("⚠️ 태그 저장 실패:", response.error);
        }
      })
      .catch(err => console.error("🔥 태그 저장 실패:", err));

  } catch (err) {
    console.error("🔥 가사 요청 또는 번역 실패:", err);
    lyricsContent.innerHTML = "⚠️ An error occurred while loading the lyrics!";
  }
}

// ✅ Apple Music 검색
function fetchTrackFromApple(query) {
  const infoContent = document.getElementById('infoContent');
  const albumCover = document.getElementById('albumCover');
  infoContent.innerHTML = "🎵 Loading Apple Music information...";

  fetch(`https://itunes.apple.com/search?term=${encodeURIComponent(query)}&entity=musicTrack&limit=1`)
    .then(res => res.json())
    .then(data => {
      if (data.results && data.results.length > 0) {
        const track = data.results[0];
        albumCover.src = track.artworkUrl100.replace('100x100', '600x600');
        infoContent.innerHTML = `
          <h3>제목: ${track.trackName}</h3>
          <p><strong>가수:</strong> ${track.artistName}</p>
          <p><strong>앨범:</strong> ${track.collectionName}</p>
          <p><strong>발매일:</strong> ${new Date(track.releaseDate).toLocaleDateString()}</p>
          <p><strong>장르:</strong> ${track.primaryGenreName}</p>
        `;
      } else {
        albumCover.src = '/static/images/default_album.png';
        infoContent.innerHTML = "🎵 Unable to find song information.";
      }
    })
    .catch(err => {
      console.error("🔥 Apple Music 검색 실패:", err);
      albumCover.src = '/static/images/default_album.png';
      infoContent.innerHTML = "⚠️ Failed to load Apple Music information!";
    });
}

// ✅ 추천어 자동완성
function handleInputChange(input, suggestionsDiv) {
  if (!suggestionsDiv) return;

  if (!input.value.trim()) {
    suggestionsDiv.style.display = 'none';
    suggestionsDiv.innerHTML = '';
    return;
  }

  if (document.activeElement !== input) return;

  const query = input.value;
  fetch(`/music/autocomplete/?q=${encodeURIComponent(query)}`)
    .then(res => res.json())
    .then(data => handleSuggestions(data, suggestionsDiv, input))
    .catch(err => console.error("🔥 자동완성 요청 실패:", err));
}

// ✅ 추천어 목록 렌더링
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

// ✅ 추천어 숨김
function hideSuggestions() {
  const suggestions = document.getElementById('suggestions');
  if (suggestions) {
    suggestions.style.display = 'none';
    suggestions.innerHTML = '';
  }
}

// ✅ 가사 번역 버튼 처리
function translateLyrics(lang) {
  const lyricsContent = document.getElementById('lyricsContent');
  const selectedLyrics = translatedLyrics[lang] || `⚠️ No lyrics for this language.`;
  lyricsContent.innerHTML = `<p>${selectedLyrics}</p>`;
}

// ✅ 검색창 입력값으로 검색 페이지 이동
function redirectSearch() {
  const query = document.getElementById('searchInput').value;
  if (query) {
    window.location.href = `/music/search/?q=${encodeURIComponent(query)}`;
  }
}
