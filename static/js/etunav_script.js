const panel = document.getElementById("panel");
const overlay = document.getElementById("overlay");
const handle = document.getElementById("handle");
const taskContainer = document.getElementById("task-container");
const detailsPanel = document.getElementById("details-panel");

let allTasks = [];
let currentFilter = 'all';

function togglePanel() {
    panel.classList.toggle("open");
    handle.classList.toggle("open");
    overlay.classList.toggle("show");
}

function closePanel() {
    panel.classList.remove("open");
    handle.classList.remove("open");
    overlay.classList.remove("show");
}

function closeDetailsPanel() {
    detailsPanel.classList.remove("open");
}

handle.addEventListener("click", togglePanel);
overlay.addEventListener("click", () => {
    closePanel();
    closeDetailsPanel();
});

window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        closePanel();
        closeDetailsPanel();
    }
});

// Brain animation
window.addEventListener('mousemove', (e) => {
    let x = (e.clientX / window.innerWidth - 0.5) * 20;
    let y = (e.clientY / window.innerHeight - 0.5) * 20;
    const brain = document.querySelector('.static-brain');
    if (brain) {
        brain.style.transform = `translate(${x}px, ${y}px) scale(0.85)`;
    }
});


// Initialization
document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboardData();
    await loadNotifications();
    setInterval(loadNotifications, 15000); // Polling toutes les 15 secondes
    lucide?.createIcons();
});

async function loadDashboardData() {
    try {
        const response = await fetch('/dashboard/data');
        const data = await response.json();

        allTasks = [];

        // Build category menu
        const menu = document.getElementById('menu');
        // keep only the 'all' item
        menu.innerHTML = `<div class="item active" onclick="filterCategory('all', this)">Toutes les démarches</div>`;

        data.categories.forEach(cat => {
            const item = document.createElement('div');
            item.className = 'item';
            item.innerHTML = `${cat.emoji} ${cat.name}`;
            item.onclick = (e) => filterCategory(cat.id, e.target);
            menu.appendChild(item);

            cat.steps.forEach(step => {
                allTasks.push({
                    id: step.id,
                    title: step.title,
                    desc: step.description,
                    icon: cat.emoji || '📄',
                    categoryId: cat.id,
                    categoryName: cat.name,
                    completed: step.completed,
                    documents: step.documents_needed,
                    sub_steps: step.sub_steps,
                    resources: step.resources
                });
            });
        });

        updateProgress(data.categories);
        renderGrid();
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function filterCategory(catId, element) {
    currentFilter = catId;

    // Update active class
    if (element) {
        document.querySelectorAll('.menu .item').forEach(el => el.classList.remove('active'));
        element.classList.add('active');
    }

    renderGrid();
    if (window.innerWidth <= 768) closePanel();
}

function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

function renderGrid() {
    if (!taskContainer) return;
    taskContainer.innerHTML = '';

    const filteredTasks = currentFilter === 'all'
        ? allTasks
        : allTasks.filter(t => t.categoryId === currentFilter);

    // Shuffle only visually, don't permute actual array so indices remain consistent
    const slots = Array.from({ length: filteredTasks.length }, (_, i) => i);
    shuffleArray(slots);

    const cardW = 300;
    const cardH = 220;
    const gap = 30;
    const headerHeight = 120;
    const screenPadding = 40;

    const availableWidth = window.innerWidth - (screenPadding * 2);
    let cols = Math.floor(availableWidth / (cardW + gap));
    if (cols < 1) cols = 1;

    const gridWidth = (cols * cardW) + ((cols - 1) * gap);
    const startX = Math.max(0, (window.innerWidth - gridWidth) / 2);
    const slotHeight = 290;

    let maxBottom = 0;

    filteredTasks.forEach((task, index) => {
        const card = document.createElement('div');
        card.className = `task-card ${task.completed ? 'completed' : ''}`;
        card.id = `task-${task.id}`;

        const slotIndex = slots[index];
        const col = slotIndex % cols;
        const row = Math.floor(slotIndex / cols);

        const baseX = startX + (col * (cardW + gap));
        const baseY = headerHeight + (row * slotHeight);

        const jitterX = (Math.random() - 0.5) * 10;
        const jitterY = (Math.random() - 0.5) * 20;

        const finalX = baseX + jitterX;
        const finalY = baseY + jitterY;

        card.style.left = `${finalX}px`;
        card.style.top = `${finalY}px`;

        const cardBottom = finalY + cardH;
        if (cardBottom > maxBottom) maxBottom = cardBottom;

        // Is the icon a remixicon class or an emoji?
        const isIconClass = task.icon.startsWith('ri-');
        const iconHtml = isIconClass
            ? `<i class="${task.icon} card-icon"></i>`
            : `<span class="card-icon" style="font-size:1.5rem;">${task.icon}</span>`;

        card.innerHTML = `
            <div class="card-header">
                <div class="card-title-row">
                    ${iconHtml}
                    <h3>${task.title}</h3>
                </div>
                <div class="task-checkbox"></div>
            </div>
            <p class="card-description">${task.desc || ''}</p>
            <button class="btn-learn-more" style="border:none; cursor:pointer;" onclick="openDetails(${task.id})">En savoir plus</button>
        `;

        const checkbox = card.querySelector('.task-checkbox');
        checkbox.addEventListener('click', async (e) => {
            e.stopPropagation();
            await toggleTaskCompletion(task.id, card);
        });

        // Make entire card clickable for details
        card.addEventListener('click', (e) => {
            if (e.target !== checkbox) {
                openDetails(task.id);
            }
        });

        taskContainer.appendChild(card);
    });

    taskContainer.style.height = `${Math.max(window.innerHeight, maxBottom + 100)}px`;
}

async function toggleTaskCompletion(stepId, card) {
    try {
        const response = await fetch(`/api/step/${stepId}/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        if (data.success) {
            // Update local state
            const task = allTasks.find(t => t.id === stepId);
            if (task) task.completed = data.completed;

            if (data.completed) {
                card.classList.add('completed');
            } else {
                card.classList.remove('completed');
            }

            // Reload global progress smoothly
            const progressRes = await fetch(`/api/progress/${window.ETUNAV_USER.id}`);
            const progressData = await progressRes.json();

            document.getElementById('progress-percentage').textContent = `${progressData.percentage}%`;
            document.getElementById('progress-bar-fill').style.width = `${progressData.percentage}%`;
            document.getElementById('progress-text').textContent = `${progressData.completed_steps}/${progressData.total_steps} étapes complétées`;
        }
    } catch (e) {
        console.error('Error toggling step:', e);
    }
}

function updateProgress(categories) {
    let total = 0;
    let completed = 0;
    categories.forEach(cat => {
        total += cat.total_steps;
        completed += cat.completed_steps;
    });

    const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
    document.getElementById('progress-percentage').textContent = `${percentage}%`;
    document.getElementById('progress-bar-fill').style.width = `${percentage}%`;
    document.getElementById('progress-text').textContent = `${completed}/${total} étapes complétées`;
}

function openDetails(taskId) {
    const task = allTasks.find(t => t.id === taskId);
    if (!task) return;

    document.getElementById('dt-icon').textContent = task.icon.startsWith('ri-') ? '📁' : task.icon;
    document.getElementById('dt-title').textContent = task.title;
    document.getElementById('dt-desc').textContent = task.desc || '';

    // Documents
    const docsContainer = document.getElementById('dt-docs');
    const docsSection = document.getElementById('dt-docs-sec');
    if (task.documents && task.documents.length) {
        docsContainer.innerHTML = task.documents.map(d => `<li>${d}</li>`).join('');
        docsSection.style.display = 'block';
    } else {
        docsSection.style.display = 'none';
    }

    // Sub-steps
    const subsContainer = document.getElementById('dt-subs');
    const subsSection = document.getElementById('dt-subs-sec');
    if (task.sub_steps && task.sub_steps.length) {
        subsContainer.innerHTML = task.sub_steps.map(s => {
            const isChecked = s.checked ? 'checked' : '';
            return `<li class="${isChecked}" onclick="this.classList.toggle('checked')">${s.text || s}</li>`;
        }).join('');
        subsSection.style.display = 'block';
    } else {
        subsSection.style.display = 'none';
    }

    // Resources
    const resContainer = document.getElementById('dt-res');
    const resSection = document.getElementById('dt-res-sec');
    if (task.resources && task.resources.length) {
        resContainer.innerHTML = task.resources.map(r => `
            <a href="${r.url}" target="_blank" class="resource-link">
                <i class="${r.icon || 'ri-external-link-line'}"></i>
                ${r.label || r.title || r.url}
            </a>
        `).join('');
        resSection.style.display = 'block';
    } else {
        resSection.style.display = 'none';
    }

    detailsPanel.classList.add('open');
}

let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(renderGrid, 200);
});

async function loadNotifications() {
    try {
        const response = await fetch('/api/notifications');
        const data = await response.json();

        const dot = document.getElementById('alertDot');
        const countText = document.getElementById('notif-count');

        if (data.unread > 0) {
            dot.classList.add('show');
            dot.style.display = 'block';
            countText.textContent = `${data.unread} nouvelle(s)`;
            dot.style.background = '#ff0000';
            dot.style.width = '10px';
            dot.style.height = '10px';
            dot.style.borderRadius = '50%';
            dot.style.position = 'absolute';
            dot.style.top = '0';
            dot.style.right = '0';
        } else {
            dot.classList.remove('show');
            dot.style.display = 'none';
            countText.textContent = `Aucune nouvelle`;
        }

        window.ETUNAV_NOTIFICATIONS = data.notifications;
    } catch (e) {
        console.error('Error loading notifs:', e);
    }
}

document.getElementById('alertBtn').addEventListener('click', async () => {
    const notifs = window.ETUNAV_NOTIFICATIONS || [];
    const unread = notifs.filter(n => !n.is_read);

    if (unread.length > 0) {
        let msg = "Vos nouvelles notifications :\n\n";
        unread.forEach(n => {
            msg += `- ${n.title} : ${n.message}\n`;
        });
        alert(msg);

        for (const n of unread) {
            await fetch(`/api/notifications/${n.id}/read`, { method: 'POST' });
        }
        loadNotifications();
    } else {
        alert("Vous n'avez aucune nouvelle notification.");
    }
});


function setupAlertsEntryPoint() {
    const alertsLink = document.getElementById('alerts-nav-link');
    if (!alertsLink) return;

    alertsLink.addEventListener('click', () => {
        try {
            localStorage.setItem('etunav_alerts_last_entry', 'dashboard_sidebar');
        } catch (e) {
            console.warn('Unable to persist alerts entry point', e);
        }
    });
}

document.addEventListener('DOMContentLoaded', setupAlertsEntryPoint);