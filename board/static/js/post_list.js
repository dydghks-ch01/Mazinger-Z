function handleScrap(button) {
  const postCard = button.closest('.post-card');
  const postId = postCard.dataset.postId;

  fetch(`/scrap/${postId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCSRFToken(),
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
  .then(response => {
    if (response.status === 403) {
      alert("로그인이 필요한 항목입니다.");
      return;
    }
    return response.json();
  })
  .then(data => {
    if (data.scrapped) {
      button.style.color = "#ff5e5e";
    } else {
      button.style.color = "#aaa";
    }
  });
}

function getCSRFToken() {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    cookie = cookie.trim();
    if (cookie.startsWith(name + '=')) {
      return decodeURIComponent(cookie.substring(name.length + 1));
    }
  }
  return '';
}

function handleScrap(button) {
  const postCard = button.closest('.post-card');
  const postId = postCard.dataset.postId;

  fetch(`/scrap/${postId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCSRFToken(),
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
  .then(response => {
    if (response.status === 403) {
      alert("로그인이 필요한 항목입니다.");
      return;
    }
    return response.json();
  })
  .then(data => {
    if (data.scrapped) {
      button.querySelector("img").src = "/static/images/scrap_on.png";
    } else {
      button.querySelector("img").src = "/static/images/scrap_off.png";
    }
  });
}

function getCSRFToken() {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    cookie = cookie.trim();
    if (cookie.startsWith(name + '=')) {
      return decodeURIComponent(cookie.substring(name.length + 1));
    }
  }
  return '';
}

// 🔐 비로그인 사용자의 스크랩 버튼 클릭 시 로그인 안내
document.addEventListener("DOMContentLoaded", function () {
  const notLoggedInButtons = document.querySelectorAll(".btn-scrap.not-logged-in");

  notLoggedInButtons.forEach(button => {
    button.addEventListener("click", function () {
      const shouldLogin = confirm("로그인이 필요한 항목입니다.\n로그인 페이지로 이동하시겠습니까?");
      if (shouldLogin) {
        const currentUrl = window.location.pathname + window.location.search;
        window.location.href = `/accounts/login/?next=${encodeURIComponent(currentUrl)}`;
      }
    });
  });
});

document.addEventListener("DOMContentLoaded", function () {
  const writeBtn = document.querySelector(".not-logged-in-write");

  if (writeBtn) {
    writeBtn.addEventListener("click", function (e) {
      e.preventDefault();
      const shouldLogin = confirm("로그인이 필요한 기능입니다.\n로그인 페이지로 이동하시겠습니까?");
      if (shouldLogin) {
        const currentUrl = window.location.pathname + window.location.search;
        window.location.href = `/accounts/login/?next=${encodeURIComponent(currentUrl)}`;
      }
    });
  }
});

