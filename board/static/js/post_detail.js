document.addEventListener('DOMContentLoaded', function () {
  // ✅ 대댓글 입력 폼 토글
  const replyButtons = document.querySelectorAll('.reply-btn');
  replyButtons.forEach(button => {
    button.addEventListener('click', function () {
      const commentId = this.getAttribute('data-id');
      const form = document.getElementById(`reply-form-${commentId}`);
      if (form) {
        form.classList.toggle('hidden');
      }
    });
  });

  // ✅ 대댓글 보기/숨기기 토글
  const toggleReplyButtons = document.querySelectorAll('.toggle-replies-btn');
  toggleReplyButtons.forEach(button => {
    button.addEventListener('click', function () {
      const parentId = this.dataset.parentId;
      const replies = document.querySelectorAll(`#reply-container-${parentId} .reply`);
      replies.forEach(reply => reply.classList.toggle('hidden'));

      // 버튼 텍스트 토글
      this.innerText = this.innerText.includes('보기') ? '▲' : '▼';
    });
  });

  // ✅ 비로그인 시 글쓰기 버튼 클릭 시 로그인 유도
  const writeBtn = document.querySelector('.btn-write.not-logged-in-write');
  if (writeBtn) {
    writeBtn.addEventListener('click', function (e) {
      e.preventDefault();
      const confirmLogin = confirm("로그인이 필요한 기능입니다. 로그인하시겠습니까?");
      if (confirmLogin) {
        window.location.href = "/accounts/login/?next=" + encodeURIComponent(window.location.pathname);
      }
    });
  }

  // ✅ 비로그인 시 스크랩 버튼 클릭 시 로그인 유도
  const scrapButtons = document.querySelectorAll('.btn-scrap.not-logged-in');
  scrapButtons.forEach(button => {
    button.addEventListener('click', function (e) {
      e.preventDefault();
      const confirmLogin = confirm("로그인이 필요한 기능입니다. 로그인하시겠습니까?");
      if (confirmLogin) {
        window.location.href = "/accounts/login/?next=" + encodeURIComponent(window.location.pathname);
      }
    });
  });

  // ✅ 댓글 작성 (Ajax + 유효성 검사)
  const commentForm = document.getElementById('comment-form');
  if (commentForm) {
    commentForm.setAttribute('novalidate', 'true');
    commentForm.addEventListener('submit', function (e) {
      e.preventDefault();

      const content = document.getElementById('id_content');
      if (!content.value.trim()) {
        alert("댓글을 입력해주세요.");
        content.focus();
        return;
      }

      fetch("", {
        method: "POST",
        headers: {
          "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
          "Accept": "application/json",
          "X-Requested-With": "XMLHttpRequest"
        },
        body: new FormData(this)
      })
        .then(response => {
          if (response.status === 403) {
            const goLogin = confirm("로그인이 필요한 기능입니다. 로그인하시겠습니까?");
            if (goLogin) {
              window.location.href = "/accounts/login/?next=" + encodeURIComponent(window.location.pathname);
            }
          } else if (response.ok) {
            location.reload();
          } else {
            return response.json().then(data => {
              alert(data.error || "댓글 등록에 실패했습니다.");
            });
          }
        })
        .catch(err => {
          alert("댓글 등록 중 오류가 발생했습니다.");
        });
    });
  }

  // ✅ 선택된 곡 좌우 스크롤
  const container = document.querySelector('.selected-song-list');
  const leftBtn = document.querySelector('.left-arrow');
  const rightBtn = document.querySelector('.right-arrow');
  let scrollInterval;

  function startScroll(direction) {
    scrollInterval = setInterval(() => {
      container.scrollLeft += direction * 5;
    }, 16);
  }

  function stopScroll() {
    clearInterval(scrollInterval);
  }

  if (leftBtn && rightBtn && container) {
    leftBtn.addEventListener('mouseenter', () => startScroll(-1));
    rightBtn.addEventListener('mouseenter', () => startScroll(1));
    leftBtn.addEventListener('mouseleave', stopScroll);
    rightBtn.addEventListener('mouseleave', stopScroll);
  }
});
