/**
 * EnglishPractice - Main Application JS
 * General utilities, dynamic dropdowns, avatar preview, alert dismissals
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto dismiss bootstrap alerts after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach((alert) => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 6000);
    });

    // 2. Dynamic Subcategory Dropdown loader (Exam Setup & Question Form)
    const parentCategorySelect = document.getElementById('parentCategorySelect');
    const subCategorySelect = document.getElementById('subCategorySelect');

    if (parentCategorySelect && subCategorySelect) {
        parentCategorySelect.addEventListener('change', function () {
            const parentId = this.value;
            subCategorySelect.innerHTML = '<option value="">-- Tất cả chủ đề con --</option>';

            if (!parentId || parentId === '0') {
                subCategorySelect.disabled = true;
                return;
            }

            fetch(`/api/categories/${parentId}/subcategories`)
                .then((res) => res.json())
                .then((data) => {
                    if (data && data.length > 0) {
                        subCategorySelect.disabled = false;
                        data.forEach((sub) => {
                            const opt = document.createElement('option');
                            opt.value = sub.id;
                            opt.textContent = sub.name;
                            subCategorySelect.appendChild(opt);
                        });
                    } else {
                        subCategorySelect.disabled = true;
                    }
                })
                .catch((err) => {
                    console.error('Error fetching subcategories:', err);
                });
        });
    }

    // 3. Avatar Upload Preview
    const avatarInput = document.getElementById('avatarInput');
    const avatarPreview = document.getElementById('avatarPreview');

    if (avatarInput && avatarPreview) {
        avatarInput.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    avatarPreview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }
});
