console.log("🧪 openLovelistModal 찾기:", document.getElementById('openLovelistModal'));

document.addEventListener('DOMContentLoaded', function () {
  const openBtn = document.getElementById('openLovelistModal');
  const closeBtn = document.getElementById('closeLovelistModal');
  const modal = document.getElementById('lovelistModal');
  const backdrop = document.getElementById('lovelistModalBackdrop');
  const preview = document.getElementById('selectedSongsPreview');
  const hiddenInputs = document.getElementById('selectedSongsHiddenInputs');

  if (!openBtn || !closeBtn || !modal || !backdrop || !preview || !hiddenInputs) {
    console.warn("❗ 요소 중 하나 이상을 찾을 수 없습니다.");
    return;
  }

  // ✅ 0. [곡 등록] 버튼 눌렀을 때 모달 열리게 하기
  openBtn.addEventListener('click', () => {
    console.log("✅ [곡 등록] 버튼 클릭 → 모달 열림");
    modal.classList.add('show');
    backdrop.classList.add('show');
  });

  // ✅ 1. [곡 선택 완료] 누르면 모달 닫기 + preview 갱신
  closeBtn.addEventListener('click', () => {
    modal.classList.remove('show');
    backdrop.classList.remove('show');

    const checkboxes = modal.querySelectorAll('input.song-checkbox:checked');
    const selectedMap = new Map();
    hiddenInputs.innerHTML = '';
    preview.innerHTML = '';

    if (checkboxes.length === 0) {
      preview.innerHTML = `<p class="no-selection">선택된 곡이 없습니다.</p>`;
      return;
    }

    let html = `<p><strong>선택된 곡:</strong></p><ul>`;

    checkboxes.forEach(cb => {
      const songId = cb.value;
      const label = cb.parentElement.textContent.trim();

      if (!selectedMap.has(songId)) {
        selectedMap.set(songId, label);

        html += `
          <li data-id="${songId}">
            ${label}
            <button type="button" class="remove-song" data-id="${songId}" style="margin-left:10px;">❌</button>
          </li>
        `;

        const hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = 'songs';
        hidden.value = songId;
        hiddenInputs.appendChild(hidden);
      }
    });

    html += `</ul>`;
    preview.innerHTML = html;

    // 삭제 버튼 연결
    preview.querySelectorAll('.remove-song').forEach(button => {
      button.addEventListener('click', (e) => {
        const id = e.target.dataset.id;
        const checkbox = modal.querySelector(`input.song-checkbox[value="${id}"]`);
        if (checkbox) checkbox.checked = false;

        e.target.closest('li').remove();
        const hidden = hiddenInputs.querySelector(`input[value="${id}"]`);
        if (hidden) hidden.remove();

        if (preview.querySelectorAll('li').length === 0) {
          preview.innerHTML = `<p class="no-selection">선택된 곡이 없습니다.</p>`;
        }
      });
    });
  });

  // ✅ 2. backdrop 클릭 시 모달 닫기
  backdrop.addEventListener('click', () => {
    modal.classList.remove('show');
    backdrop.classList.remove('show');
  });

  // ✅ 3. 초기 로드 시 previouslySelectedSongIds로 미리보기 구성
  setTimeout(() => {
    if (typeof previouslySelectedSongIds !== 'undefined' && previouslySelectedSongIds.length > 0) {
      let html = `<p><strong>선택된 곡:</strong></p><ul>`;
      hiddenInputs.innerHTML = '';

      previouslySelectedSongIds.forEach(id => {
        const checkbox = document.querySelector(`input.song-checkbox[value="${id}"]`);
        if (checkbox) {
          checkbox.checked = true;
          const label = checkbox.parentElement.textContent.trim();

          html += `
            <li data-id="${id}">
              ${label}
              <button type="button" class="remove-song" data-id="${id}" style="margin-left:10px;">❌</button>
            </li>
          `;

          const hidden = document.createElement('input');
          hidden.type = 'hidden';
          hidden.name = 'songs';
          hidden.value = id;
          hiddenInputs.appendChild(hidden);
        } else {
          console.warn("❌ checkbox 못 찾음:", id);
        }
      });

      html += `</ul>`;
      preview.innerHTML = html;
    }
  }, 0);
});
