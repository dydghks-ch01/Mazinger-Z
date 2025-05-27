// ✅ 모달 및 폼 요소들 선언
let passwordModal, editModal;
let nicknameInput, birthdayInput, phoneInput, profileSelect, submitBtn;
let jsNicknameError, jsPhoneError;
let originalValues = {};  // 초기 입력값 저장 (변경 감지용)

// 🔓 비밀번호 확인 모달 열기
function openPasswordModal() {
  passwordModal.classList.add("show");
}

// 🔐 비밀번호 확인 모달 닫기
function closePasswordModal() {
  passwordModal.classList.remove("show");
}

// ✏️ 프로필 수정 모달 열기
function openModal() {
  editModal.classList.add("show");
  updateSubmitState();  // 수정 가능한 상태인지 체크
}

// 🔁 프로필 수정 모달 닫기
function closeModal() {
  editModal.classList.remove("show");
}

// 🧪 닉네임 유효성 검사 (한글, 영문, 숫자, 밑줄만 허용 + 욕설 감지)
const badWords = ["시발", "병신", "개새끼", "fuck", "shit", "asshole"];  // 🚀 추가

function validateNickname(nickname) {
  const basicValid = /^[\w가-힣]+$/.test(nickname);
  const hasBadWord = badWords.some(word => nickname.includes(word));
  return basicValid && !hasBadWord;  // 🚀 욕설 있으면 false 반환
}

// ✅ 닉네임 중복 검사 (백엔드 AJAX)
function checkNicknameDuplicate(nickname, callback) {
  fetch(`/accounts/check_nickname/?nickname=${encodeURIComponent(nickname)}`)
    .then(res => res.json())
    .then(data => {
      nicknameInput.dataset.duplicate = data.duplicate;
      callback();
    })
    .catch(err => {
      console.error("중복 닉네임 확인 오류:", err);
      nicknameInput.dataset.duplicate = "false";
      callback();
    });
}

// 📱 전화번호 자동 포맷 (예: 010-1234-5678)
function formatPhoneNumber(value) {
  const cleaned = value.replace(/\D/g, "").slice(0, 11);  // 숫자만 추출, 11자리까지
  if (cleaned.length < 4) return cleaned;
  if (cleaned.length < 8) return `${cleaned.slice(0, 3)}-${cleaned.slice(3)}`;
  return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 7)}-${cleaned.slice(7)}`;
}

// 📞 전화번호 유효성 검사
function validatePhoneNumber(콜) {
  return /^010-\d{4}-\d{4}$/.test(콜);
}

// 🔄 제출 버튼 활성화 여부 갱신
function updateSubmitState() {
  const currentValues = {
    nickname: nicknameInput.value.trim(),
    birthday: birthdayInput.value,
    phone: phoneInput.value.trim(),
    picture: profileSelect.value
  };

  // 어떤 필드든 값이 변경되었는지 확인
  const changed = Object.keys(currentValues).some(
    key => currentValues[key] !== originalValues[key]
  );

  // 유효성 검사
  const nicknameValid = validateNickname(currentValues.nickname);
  const phoneValid = validatePhoneNumber(currentValues.phone);
  const isDuplicate = nicknameInput.dataset.duplicate === "true";

  // 모든 조건 만족 시 수정 버튼 활성화
  submitBtn.disabled = !(nicknameValid && phoneValid && !isDuplicate && changed);

  // ⚠️ 닉네임 오류 표시
  if (!nicknameValid) {
    nicknameInput.style.border = "2px solid red";
    if (badWords.some(word => nicknameInput.value.includes(word))) {
      jsNicknameError.innerText = "닉네임에 부적절한 단어가 포함되었습니다.";
    } else {
      jsNicknameError.innerText = "한글, 영문, 숫자, 밑줄(_)만 사용할 수 있습니다.";
    }
  } else if (isDuplicate) {
    nicknameInput.style.border = "2px solid red";
    jsNicknameError.innerText = "이미 사용 중인 닉네임입니다.";
  } else {
    nicknameInput.style.border = "2px solid green";
    jsNicknameError.innerText = "";
  }

  // ⚠️ 전화번호 오류 표시
  if (!phoneValid) {
    phoneInput.style.border = "2px solid red";
    jsPhoneError.innerText = "전화번호는 010-1234-5678 형식이어야 합니다.";
  } else {
    phoneInput.style.border = "2px solid green";
    jsPhoneError.innerText = "";
  }
}

// 🔐 비밀번호 확인 후 모달 열기
function verifyPassword() {
  const password = document.getElementById("confirmPassword").value;
  if (password.trim() === "") {
    alert("비밀번호를 입력하세요.");
    return;
  }

  // ✅ HTML의 <meta name="csrf-token"> 에서 CSRF 토큰 가져오기
  const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

  // ✅ 서버로 비밀번호 확인 요청 보내기
  fetch("verify_password/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken
    },
    body: JSON.stringify({ password: password })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      document.getElementById("hiddenPassword").value = password;  // 다음 요청을 위해 저장
      closePasswordModal();
      openModal();
    } else {
      alert("비밀번호가 올바르지 않습니다.");
    }
  })
  .catch(err => {
    console.error("비밀번호 확인 오류:", err);
    alert("서버 오류가 발생했습니다.");
  });
}

// 🧩 전역 접근 가능하게 함수 등록
window.verifyPassword = verifyPassword;
window.openModal = openModal;
window.closeModal = closeModal;
window.closePasswordModal = closePasswordModal;

// ✅ 문서 로딩 완료 시 DOM 초기화
document.addEventListener("DOMContentLoaded", function () {
  const firstBtn = document.querySelector('.mypage-link-btn.lyrics-btn');
  if (firstBtn) firstBtn.click();
  // 🔗 DOM 요소 캐싱
  passwordModal = document.getElementById("passwordModal");
  editModal = document.getElementById("editModal");
  const openBtn = document.getElementById("openPasswordBtn");

  nicknameInput = document.getElementById("id_nickname");
  birthdayInput = document.getElementById("id_birthday");
  phoneInput = document.getElementById("id_phone_number");
  profileSelect = document.getElementById("id_profile_picture");
  submitBtn = document.getElementById("submit-btn");

  // 🧨 닉네임 오류 메시지 표시용 <p> 추가
  jsNicknameError = document.createElement("p");
  jsNicknameError.classList.add("error");
  jsNicknameError.style.color = "red";
  nicknameInput.insertAdjacentElement("afterend", jsNicknameError);

  // 🧨 전화번호 오류 메시지 표시용 <p> 추가
  jsPhoneError = document.createElement("p");
  jsPhoneError.classList.add("error");
  jsPhoneError.style.color = "red";
  phoneInput.insertAdjacentElement("afterend", jsPhoneError);

  // 🧾 현재 입력값 저장 (변경 감지용)
  originalValues = {
    nickname: nicknameInput.value.trim(),
    birthday: birthdayInput.value,
    phone: phoneInput.value.trim(),
    picture: profileSelect.value
  };

  // ✅ 수정 버튼 클릭 이벤트
  if (openBtn) openBtn.addEventListener("click", openPasswordModal);

  // ✅ 실시간 닉네임 변경 감지 및 중복 확인
  nicknameInput.addEventListener("input", () => {
    const value = nicknameInput.value.trim();
    if (!validateNickname(value)) {
      nicknameInput.dataset.duplicate = "false";
      updateSubmitState();
      return;
    }
    checkNicknameDuplicate(value, updateSubmitState);
  });

  // ✅ 생일 변경 시 상태 갱신
  birthdayInput.addEventListener("change", updateSubmitState);

  // ✅ 전화번호 입력 시 자동 포맷 + 상태 갱신
  phoneInput.addEventListener("input", () => {
    const formatted = formatPhoneNumber(phoneInput.value);
    phoneInput.value = formatted;
    updateSubmitState();
  });

  // ✅ 프로필 이미지 변경 시 미리보기 갱신
  profileSelect.addEventListener("change", () => {
    const previewImg = document.getElementById("profilePreview");
    previewImg.src = `/static/images/profiles/${profileSelect.value}`;
    updateSubmitState();
  });

  // ✅ 최초 로딩 시 닉네임 중복 여부 초기 검사
  checkNicknameDuplicate(nicknameInput.value.trim(), updateSubmitState);
});

const itemsPerPage = 10;
let allLyricsData = [];


// ✅ 전체 가사 목록 불러오기 + 초기 렌더링
function loadLyricsTable(page = 1) {
  const table = document.getElementById('user-lyrics-table');
  table.style.display = 'table';

  fetch('/accounts/user-generated-lyrics/')
    .then(res => res.json())
    .then(data => {
      allLyricsData = data.lyrics || [];
      renderLyricsPage(page);
    })
    .catch(error => {
      console.error('❌ 가사 불러오기 실패:', error);
    });
}

// ✅ 현재 페이지의 가사 목록 렌더링
function renderLyricsPage(page) {
  const tbody = document.getElementById('user-lyrics-body');
  tbody.innerHTML = '';

  const start = (page - 1) * itemsPerPage;
  const pageData = allLyricsData.slice(start, start + itemsPerPage);

  if (pageData.length === 0) {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td><input type="checkbox" disabled></td>
      <td colspan="3">등록된 가사가 없습니다.</td>
    `;
    tbody.appendChild(row);
    return;
  }

  pageData.forEach(item => {
    const row = document.createElement('tr');
    row.dataset.lyricId = item.id;

    console.log("이미지 경로 확인:", item.image_file);

    const imageTag = item.image_file
    ? `<img src="${item.image_file}" alt="cover" class="preview-thumbnail" data-src="${item.image_file}" style="width:60px;height:60px;object-fit:cover;border-radius:4px;">`
    : `<div style="width:60px;height:60px;background:#444;border-radius:4px;"></div>`;

    row.innerHTML = `
      <td><input type="checkbox"></td>
      <td style="text-align:left">${imageTag}</td>
      <td class="clickable-title">${item.prompt} (${item.style}/${item.language})</td>
      <td>${item.created_at || '날짜 없음'}</td>
    `;

    // ✅ 제목(td)만 클릭 시 페이지 이동
    row.querySelector('.clickable-title').addEventListener('click', () => {
      sessionStorage.removeItem('modal_once_shown');
      window.location.href = `/lyricsgen/?open_id=${item.id}`;
    });

    tbody.appendChild(row);
  });

  renderPagination(Math.ceil(allLyricsData.length / itemsPerPage), page, renderLyricsPage);
  bindSelectAll();
}


// ✅ 범용 페이지네이션 함수 (콜백 함수 전달 방식)
function renderPagination(totalPages, currentPage, renderFunction) {
  const pagination = document.getElementById("pagination");
  pagination.innerHTML = '';

  const safeTotalPages = Math.max(totalPages, 1);  // 최소 1 페이지는 표시

  for (let i = 1; i <= safeTotalPages; i++) {
    const button = document.createElement('button');
    button.textContent = i;

    if (i === currentPage) {
      button.classList.add('active');
    }

    // 클릭 시 전달받은 renderFunction 사용
    button.addEventListener('click', () => renderFunction(i));

    pagination.appendChild(button);
  }
}

// ---------------------------------------------------------------------변경끝끝 진섭섭

// ✅ 체크박스 전체 선택 기능
function bindSelectAll() {
  const selectAllCheckbox = document.getElementById('select-all');
  if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener('change', function () {
      const checkboxes = document.querySelectorAll('#user-lyrics-body input[type="checkbox"]');
      checkboxes.forEach(cb => cb.checked = this.checked);
    });
  }
}

// ✅ 버튼 클릭 시 동작
document.querySelectorAll('.mypage-link-btn').forEach(btn => {
  btn.addEventListener('click', function () {
    document.querySelectorAll('.mypage-link-btn').forEach(b => b.classList.remove('active'));
    this.classList.add('active');

    const type = this.dataset.type;
    if (type === "lyrics") {
      loadLyricsTable();
    } else if (type === "button2") {
      loadUserPosts();
    } else if (type === "button3") {
      loadUserLovelist();  // ✅ 추가
    } else if (type === "button4") {
      loadSupportList();  // ✅ 추가
    }
  });
});





// 추가 진섭섭





// ✅ 첫 페이지 진입 시 자동으로 "내가 만든 가사" 클릭
document.getElementById('delete-selected').addEventListener('click', function () {
  const checkedRows = document.querySelectorAll('#user-lyrics-body tr input[type="checkbox"]:checked');
  if (checkedRows.length === 0) {
    alert("삭제할 항목을 선택하세요.");
    return;
  }

  const currentTab = document.querySelector('.mypage-link-btn.active').dataset.type;
  const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

  // 1. 내가 만든 가사
  if (currentTab === "lyrics") {
    const idsToDelete = Array.from(checkedRows).map(cb => cb.closest('tr').dataset.lyricId);
    if (!confirm("정말 삭제하시겠습니까?")) return;

    fetch('/accounts/delete-lyrics/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({ ids: idsToDelete })
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          alert("삭제되었습니다.");
          loadLyricsTable();
        } else {
          alert("삭제 실패. 다시 시도해주세요.");
        }
      })
      .catch(err => {
        console.error("❌ 가사 삭제 요청 실패:", err);
      });

  // 2. 게시글 (지원 시)
  } else if (currentTab === "button2") {
    const postIds = Array.from(checkedRows).map(cb => cb.closest('tr').dataset.postId);
    if (!confirm("선택한 게시글을 삭제하시겠습니까?")) return;

    Promise.all(postIds.map(id =>
      fetch(`/board/post/${id}/delete/ajax/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken }
      })
    ))
      .then(() => {
        alert("삭제되었습니다.");
        loadUserPosts();
      })
      .catch(err => {
        console.error("❌ 게시글 삭제 실패:", err);
      });

  // 3. 좋아요 목록 (지원 시)
  } else if (currentTab === "button3") {
    const data = Array.from(checkedRows).map(cb => {
      const row = cb.closest('tr');
      return {
        title: row.dataset.title,
        artist: row.dataset.artist
      };
    });

    if (!confirm("선택한 곡을 좋아요 목록에서 삭제하시겠습니까?")) return;

    Promise.all(data.map(item =>
      fetch('/toggle-like/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(item)
      })
    ))
      .then(() => {
        alert("삭제되었습니다.");
        loadUserLovelist();
      })
      .catch(err => {
        console.error("❌ 좋아요 삭제 실패:", err);
      });

  // 4. 고객센터 문의글
  } else if (currentTab === "button4") {
    const postIds = Array.from(checkedRows).map(cb => cb.closest('tr').dataset.postId);
    if (!confirm("선택한 문의글을 삭제하시겠습니까?")) return;

    Promise.all(postIds.map(id =>
      fetch(`/support/${id}/delete/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken }
      })
    ))
      .then(() => {
        alert("삭제되었습니다.");
        loadSupportList();
      })
      .catch(err => {
        console.error("❌ 문의글 삭제 실패:", err);
      });
  }
});



// 진섭 추가 5월19일
// ✅ 헤더 템플릿 정의
const headerTemplates = {
  lyrics: `
    <tr class="table-header">
      <th class="col-select"><input type="checkbox" id="select-all" title="전체 선택"></th>
      <th class="col-image">미리보기</th>
      <th class="col-title">
        <span class="th-title-main">제목</span>
        <span class="th-title-sub"> (장르 / 언어)</span>
      </th>
      <th class="col-date">작성일</th>
    </tr>`,
    button2: `
    <tr class="table-header">
      <th><input type="checkbox" id="select-all" title="전체 선택"></th>
      <th>제목</th>
      <th>좋아요수</th>
      <th>작성일</th>
    </tr>`,
  button3: `
    <tr class="table-header">
      <th class="col-select"><input type="checkbox" id="select-all" title="전체 선택"></th>
      <th>좋아요한 곡</th>
      <th>아티스트</th>
      <th>작성일</th>
    </tr>`,
  button4: `
    <tr class="table-header">
      <th class="col-select"><input type="checkbox" id="select-all" title="전체 선택"></th>
      <th>문의 제목</th>
      <th>처리 상태</th>
      <th>작성일</th>
    </tr>`
};

// ✅ 버튼 클릭 시 헤더 + 테이블 구조 변경
document.querySelectorAll('.mypage-link-btn').forEach(btn => {
  btn.addEventListener('click', function () {
    // 버튼 스타일 리셋 및 활성화
    document.querySelectorAll('.mypage-link-btn').forEach(b => b.classList.remove('active'));
    this.classList.add('active');

    const type = this.dataset.type;

    // 테이블 헤더 변경
    const thead = document.getElementById('table-head');
    thead.innerHTML = headerTemplates[type] || '';

    // 테이블 표시
    const table = document.getElementById('user-lyrics-table');
    table.style.display = 'table';

    // lyrics 탭일 경우 실제 데이터 렌더링
    if (type === "lyrics") {
      loadLyricsTable();
      return;
    }

    // 그 외 탭은 빈 행 생성 (체크박스 포함)
    const tbody = document.getElementById('user-lyrics-body');
    tbody.innerHTML = ''; // 초기화

    // 헤더의 컬럼 수 파악
    const colCount = document.querySelectorAll('#table-head tr th').length;

    const row = document.createElement('tr');

    // ✅ 체크박스 열
    const checkboxTd = document.createElement('td');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.disabled = true;  // 데이터 없음 → 비활성화
    checkboxTd.appendChild(checkbox);
    row.appendChild(checkboxTd);

    // ✅ 나머지 열
    for (let i = 1; i < colCount; i++) {
      const td = document.createElement('td');
      td.textContent = i === 1 ? '아직 구현되지 않았습니다.' : '';
      row.appendChild(td);
    }

    tbody.appendChild(row);
  });
});

// 게시판버튼 
let allPostData = [];  // 🔸 게시글 전체 데이터를 전역 변수에 저장

// ✅ 게시글 로딩 함수 (page는 1로 고정)
function loadUserPosts(page = 1) {
  const table = document.getElementById('user-lyrics-table');
  table.style.display = 'table';

  fetch('/board/user-posts/')
    .then(res => res.json())
    .then(data => {
      allPostData = data.posts || [];
      renderPostPage(page);  // 🔸 별도 렌더링 함수 호출
    })
    .catch(err => {
      console.error("❌ 게시글 불러오기 실패:", err);
    });
}

// ✅ 게시글 렌더링 함수 (페이지 기반)
function renderPostPage(page) {
  const tbody = document.getElementById('user-lyrics-body');
  tbody.innerHTML = '';

  const start = (page - 1) * itemsPerPage;
  const pageData = allPostData.slice(start, start + itemsPerPage);

  if (pageData.length === 0) {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td><input type="checkbox" disabled></td>
      <td colspan="3">등록된 게시글이 없습니다.</td>
    `;
    tbody.appendChild(row);
  } else {
    pageData.forEach(post => {
      const row = document.createElement('tr');
      row.dataset.postId = post.id;
      row.innerHTML = `
        <td><input type="checkbox"></td>
        <td>${post.title}</td>
        <td>${post.like_count ?? 0}명 좋아요</td>
        <td>${post.created_at}</td>
      `;
      row.addEventListener('click', (e) => {
        if (e.target.tagName.toLowerCase() !== 'input') {
          window.location.href = `/board/post/${post.id}/`;
        }
      });
      tbody.appendChild(row);
    });
  }

  // ✅ 페이지네이션 표시 (콜백 함수도 함께 넘김)
  const totalPages = Math.ceil(allPostData.length / itemsPerPage);
  renderPagination(totalPages, page, renderPostPage);

  bindSelectAll();  // 전체선택 기능도 유지
}


// 러브리스트 불러오기
function loadUserLovelist(page = 1) {
  const table = document.getElementById('user-lyrics-table');
  table.style.display = 'table';

  fetch('/mypage/user-lovelist/')
    .then(res => res.json())
    .then(data => {
      allLoveData = data.songs || [];  // 전역 배열에 저장
      renderLovePage(page);            // 해당 페이지 렌더링
    })
    .catch(err => {
      console.error("❌ 좋아요 목록 불러오기 실패:", err);
    });
}



// 고객센터 불러오기
let allSupportData = [];

function loadSupportList(page = 1) {
  const table = document.getElementById('user-lyrics-table');
  table.style.display = 'table';

  fetch('/mypage/json/')  // ✅ JSON API 호출
    .then(res => res.json())
    .then(data => {
      allSupportData = data.posts || [];
      renderSupportPage(page);
    })
    .catch(err => {
      console.error("❌ 고객센터 목록 불러오기 실패:", err);
    });
}

function renderSupportPage(page) {
  const tbody = document.getElementById('user-lyrics-body');
  tbody.innerHTML = '';

  const start = (page - 1) * itemsPerPage;
  const pageData = allSupportData.slice(start, start + itemsPerPage);

  if (pageData.length === 0) {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td><input type="checkbox" disabled></td>
      <td colspan="3">문의글이 없습니다.</td>
    `;
    tbody.appendChild(row);
    return;
  }

  pageData.forEach(post => {
    const row = document.createElement('tr');
    row.dataset.postId = post.id;

    row.innerHTML = `
      <td><input type="checkbox"></td>
      <td>[${post.category}] ${post.title}</td>
      <td>${post.status}</td>
      <td>${post.created_at}</td>
    `;

    row.addEventListener('click', (e) => {
      if (e.target.tagName.toLowerCase() !== 'input') {
        window.location.href = `/support/${post.id}/`;
      }
    });

    tbody.appendChild(row);
  });

  renderPagination(Math.ceil(allSupportData.length / itemsPerPage), page, renderSupportPage);
  bindSelectAll();
}


// 위에 이것도추가한거 기억 ㄱㄱㄱ
// const firstBtn = document.querySelector('.mypage-link-btn.lyrics-btn');
// if (firstBtn) firstBtn.click();

function renderLovePage(page) {
  const tbody = document.getElementById('user-lyrics-body');
  tbody.innerHTML = '';

  const start = (page - 1) * itemsPerPage;
  const pageData = allLoveData.slice(start, start + itemsPerPage);

  if (pageData.length === 0) {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td><input type="checkbox" disabled></td>
      <td colspan="3">좋아요한 곡이 없습니다.</td>
    `;
    tbody.appendChild(row);
    return;
  }

  pageData.forEach(song => {
    const row = document.createElement('tr');
    row.dataset.title = song.title;
    row.dataset.artist = song.artist;

    row.innerHTML = `
      <td><input type="checkbox"></td>
      <td>${song.title}</td>
      <td>${song.artist}</td>
      <td>${song.created_at}</td>
    `;

    row.addEventListener('click', (e) => {
      if (e.target.tagName.toLowerCase() !== 'input') {
        const query = new URLSearchParams({
          title: song.title,
          artist: song.artist
        }).toString();
        window.location.href = `/music-info/?${query}`;
      }
    });

    tbody.appendChild(row);
  });

  renderPagination(Math.ceil(allLoveData.length / itemsPerPage), page, renderLovePage);
  bindSelectAll();
}


// ✅ 이미지 클릭 시 확대 보기
document.addEventListener('click', function (e) {
  const modal = document.getElementById('imagePreviewModal');
  const modalImg = document.getElementById('previewImage');

  if (e.target.classList.contains('preview-thumbnail')) {
    e.stopPropagation();  // 부모 클릭 방지
    modalImg.src = e.target.dataset.src;
    modal.style.display = 'flex';
  } else if (e.target.id === 'imagePreviewModal') {
    modal.style.display = 'none';
  }
});

document.addEventListener('click', function (e) {
  const modal = document.getElementById('imagePreviewModal');
  const modalImg = document.getElementById('previewImage');
  const closeBtn = document.getElementById('closePreviewBtn');

  if (e.target.classList.contains('preview-thumbnail')) {
    e.stopPropagation();  // 부모 클릭 방지
    modalImg.src = e.target.dataset.src;
    modal.style.display = 'flex';
  }

  // 모달 배경이나 X 버튼 클릭 시 닫기
  if (e.target.id === 'imagePreviewModal' || e.target.id === 'closePreviewBtn') {
    modal.style.display = 'none';
  }
});