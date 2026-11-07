/**
 * Oh-My-Antigravity Interactive Features
 * Zero-dependency modern ES logic
 */

document.addEventListener('DOMContentLoaded', () => {
  initQuickstartTabs();
  initPipelineInspector();
  initAgentFilter();
  initSkillsCatalog();
  initFaqAccordion();
  initLanguageSwitcher();
});

// Toast notification helper
function showToast(message) {
  let toast = document.getElementById('oma-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'oma-toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#22D3EE" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
    <span>${message}</span>
  `;
  toast.classList.add('show');
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => {
    toast.classList.remove('show');
  }, 2200);
}

// 1. Quickstart Installation Tabs
function initQuickstartTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn[data-snippet]');
  const codeEl = document.getElementById('terminal-code-snippet');
  const copyBtn = document.getElementById('terminal-copy-btn');
  if (!tabBtns.length || !codeEl) return;

  const snippets = {
    'agy': 'agy plugin install https://github.com/HengWeiBin/oh-my-antigravity.git',
    'curl': 'curl -fsSL https://raw.githubusercontent.com/HengWeiBin/oh-my-antigravity/main/install.sh | bash',
    'powershell': 'irm https://raw.githubusercontent.com/HengWeiBin/oh-my-antigravity/main/install.ps1 | iex',
    'git': 'git clone https://github.com/HengWeiBin/oh-my-antigravity.git ~/.gemini/config/plugins/oh-my-antigravity'
  };

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const key = btn.dataset.snippet;
      if (snippets[key]) {
        codeEl.textContent = snippets[key];
      }
    });
  });

  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      const textToCopy = codeEl.textContent.trim();
      navigator.clipboard.writeText(textToCopy).then(() => {
        copyBtn.classList.add('copied');
        const origText = copyBtn.querySelector('.copy-btn-text')?.textContent || 'Copy';
        const isZh = document.documentElement.lang.startsWith('zh');
        if (copyBtn.querySelector('.copy-btn-text')) {
          copyBtn.querySelector('.copy-btn-text').textContent = isZh ? '已複製！' : 'Copied!';
        }
        showToast(isZh ? '指令已複製至剪貼簿！' : 'Command copied to clipboard!');
        setTimeout(() => {
          copyBtn.classList.remove('copied');
          if (copyBtn.querySelector('.copy-btn-text')) {
            copyBtn.querySelector('.copy-btn-text').textContent = origText;
          }
        }, 2000);
      });
    });
  }
}

// 2. Hook Pipeline Inspector
function initPipelineInspector() {
  const cards = document.querySelectorAll('.pipeline-card[data-phase]');
  const detailBox = document.getElementById('pipeline-detail');
  if (!cards.length || !detailBox) return;

  const isZh = document.documentElement.lang.startsWith('zh');

  const phaseData = {
    'session_start': {
      title: isZh ? '會話啟動階段 (SessionStart)' : 'Session Initialization (SessionStart)',
      script: 'scripts/session_start.py',
      timing: isZh ? '在每個對話會話建立時自動執行一次' : 'Fires once upon conversational session creation',
      action: isZh ? '環境探測' : 'Environment & Capability Probing',
      desc: isZh 
        ? '評估工作區能力並推薦最佳工具（如在偵測到 .codegraph 與 CodeGraph MCP 啟動時推薦 codegraph_explore 進行全庫符號解析）。'
        : 'Evaluates workspace capabilities and recommends optimal tools (such as codegraph_explore when .codegraph and CodeGraph MCP are active).',
      gate: isZh ? '唯讀環境探測，無阻擋行為。' : 'Read-only capability detection, zero blocking gates.'
    },
    'pre_invocation': {
      title: isZh ? '對話調用前階段 (PreInvocation)' : 'Pre-Turn Dynamic Context (PreInvocation)',
      script: 'scripts/pre_invocation.py',
      timing: isZh ? '在每次使用者提示詞送達代理前執行' : 'Fires at the start of each user prompt turn',
      action: isZh ? '技能動態載入與計畫鎖定' : 'Dynamic Skill Mounting & Plan Locking',
      desc: isZh 
        ? '掃描提示詞中的斜線指令（如 /debugging 或 /programming）動態掛載對應 SKILL.md，鎖定進行中待辦事項與計畫連續性，並注入代理使用提示。'
        : 'Scans prompt for slash-command triggers (e.g., /debugging) to mount matching skills, enforces plan continuation, and injects agent usage reminders.',
      gate: isZh ? '上下文注入與規範保證。' : 'Context expansion and prompt guardrails.'
    },
    'pre_tool_use': {
      title: isZh ? '工具執行前階段 (PreToolUse)' : 'Pre-Tool Security Gate (PreToolUse)',
      script: 'scripts/pre_tool_use.py',
      timing: isZh ? '在變更型工具 (write_to_file, replace_file_content, run_command) 執行前攔截' : 'Intercepts mutating tool calls before execution',
      action: isZh ? '角色權限守衛' : 'Role-Based Permission Enforcement',
      desc: isZh 
        ? '實施基於角色的嚴格權限邊界：主調度指揮官（sisyphus, atlas, prometheus）嚴禁直接修改原始碼；實作工匠（hephaestus, sisyphus-junior）嚴禁竄改外掛配置與規則。'
        : 'Enforces strict role boundaries: Orchestrators (sisyphus, atlas, prometheus) are blocked from mutating source code; Workers cannot alter plugin manifests or rules.',
      gate: isZh ? '違規即刻阻擋並要求委派至適當代理。' : 'Non-bypassable role barrier; violations blocked and redirected.'
    },
    'post_tool_use': {
      title: isZh ? '工具執行後階段 (PostToolUse)' : 'Post-Execution Verification (PostToolUse)',
      script: 'scripts/post_tool_use.py',
      timing: isZh ? '在子代理執行完畢或檔案變更完成後觸發' : 'Fires after subagent completion or file modification',
      action: isZh ? '四階段嚴格驗證協議' : '4-Phase Verification Protocol',
      desc: isZh 
        ? '強制執行親自檢閱檔案、自動化測試、品質驗證與關卡審查四階段協議；同時檢驗程式碼註解品質，並防範子代理空回應或任務漂移。'
        : 'Enforces the 4-Phase Verification Protocol (Read diffs, run tests, verify visually, pass gate). Validates code comments and catches empty responses.',
      gate: isZh ? '未達驗證標準強制要求繼續修正。' : 'Verification failure triggers mandatory correction loop.'
    },
    'stop': {
      title: isZh ? '結束階段 (Stop)' : 'Session Finalization (Stop)',
      script: 'scripts/stop.py',
      timing: isZh ? '在會話結束或代理宣告完成時執行' : 'Fires on session termination or agent completion claim',
      action: isZh ? '計畫連續性維護與指標記錄' : 'Plan Continuity & Scratch Cleanup',
      desc: isZh 
        ? '若待辦計畫中仍有未完成之任務，強制中斷代理的提早終止並要求繼續推進；任務全數完成時清理暫存資料並記錄指標。'
        : 'Intercepts premature stops if tasks remain unfinished, forcing agent continuation until 100% done; cleans up scratch files on complete finish.',
      gate: isZh ? '計畫未達 100% 絕不允許提早收工。' : '100% or nothing gate; uncompleted plans cannot exit.'
    }
  };

  cards.forEach(card => {
    card.addEventListener('click', () => {
      cards.forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      const phase = card.dataset.phase;
      const data = phaseData[phase];
      if (!data) return;

      detailBox.innerHTML = `
        <div class="detail-header">
          <div class="detail-title">
            <span>${data.title}</span>
          </div>
          <span class="detail-script">${data.script}</span>
        </div>
        <div class="detail-grid">
          <div class="detail-item">
            <h4>${isZh ? '觸發時機' : 'Trigger Point'}</h4>
            <p>${data.timing}</p>
          </div>
          <div class="detail-item">
            <h4>${isZh ? '核心機制' : 'Key Mechanism'}</h4>
            <p>${data.action}</p>
          </div>
          <div class="detail-item" style="grid-column: 1 / -1;">
            <h4>${isZh ? '詳細說明' : 'Description'}</h4>
            <p>${data.desc}</p>
          </div>
          <div class="detail-item" style="grid-column: 1 / -1;">
            <h4>${isZh ? '安全防護守衛' : 'Security Gate'}</h4>
            <p style="color: var(--accent-cyan-light); font-weight: 600;">${data.gate}</p>
          </div>
        </div>
      `;
    });
  });
}

// 3. Agent Roster Filter
function initAgentFilter() {
  const pills = document.querySelectorAll('.filter-pill[data-agent-filter]');
  const cards = document.querySelectorAll('.agent-card[data-category]');
  if (!pills.length || !cards.length) return;

  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const cat = pill.dataset.agentFilter;

      cards.forEach(card => {
        if (cat === 'all' || card.dataset.category === cat) {
          card.style.display = 'flex';
        } else {
          card.style.display = 'none';
        }
      });
    });
  });
}

// 4. Skills Catalog Search & Filter
function initSkillsCatalog() {
  const searchInput = document.getElementById('skill-search');
  const catPills = document.querySelectorAll('.filter-pill[data-skill-cat]');
  const skillCards = document.querySelectorAll('.skill-card');
  const countDisplay = document.getElementById('skills-count');
  const noResults = document.getElementById('skills-no-results');
  if (!skillCards.length) return;

  let activeCat = 'all';
  let searchQuery = '';

  function filterSkills() {
    let visibleCount = 0;
    const q = searchQuery.toLowerCase().trim();

    skillCards.forEach(card => {
      const cardCat = card.dataset.category || '';
      const cmd = (card.dataset.cmd || '').toLowerCase();
      const name = (card.dataset.name || '').toLowerCase();
      const desc = (card.querySelector('.skill-desc')?.textContent || '').toLowerCase();

      const catMatches = activeCat === 'all' || cardCat === activeCat;
      const queryMatches = !q || cmd.includes(q) || name.includes(q) || desc.includes(q);

      if (catMatches && queryMatches) {
        card.style.display = 'flex';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });

    if (countDisplay) {
      const isZh = document.documentElement.lang.startsWith('zh');
      countDisplay.textContent = isZh 
        ? `顯示 ${visibleCount} / ${skillCards.length} 項技能`
        : `Showing ${visibleCount} of ${skillCards.length} skills`;
    }

    if (noResults) {
      noResults.style.display = visibleCount === 0 ? 'block' : 'none';
    }
  }

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value;
      filterSkills();
    });
  }

  catPills.forEach(pill => {
    pill.addEventListener('click', () => {
      catPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeCat = pill.dataset.skillCat;
      filterSkills();
    });
  });

  // Click skill card to copy slash command
  skillCards.forEach(card => {
    card.addEventListener('click', () => {
      const cmd = card.dataset.cmd;
      if (cmd) {
        navigator.clipboard.writeText(cmd).then(() => {
          const isZh = document.documentElement.lang.startsWith('zh');
          showToast(isZh ? `已複製指令 ${cmd}` : `Copied command ${cmd}`);
        });
      }
    });
  });
}

// 5. FAQ Accordion
function initFaqAccordion() {
  const items = document.querySelectorAll('.faq-item');
  items.forEach(item => {
    const question = item.querySelector('.faq-question');
    if (question) {
      question.addEventListener('click', () => {
        const isOpen = item.classList.contains('open');
        // Close all others
        items.forEach(i => {
          i.classList.remove('open');
          i.querySelector('.faq-question')?.setAttribute('aria-expanded', 'false');
        });
        if (!isOpen) {
          item.classList.add('open');
          question.setAttribute('aria-expanded', 'true');
        }
      });
    }
  });
}

// 6. Language Switcher
function initLanguageSwitcher() {
  const switchBtns = document.querySelectorAll('.lang-btn[data-lang]');
  if (!switchBtns.length) return;

  switchBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetLang = btn.dataset.lang;
      localStorage.setItem('oma_lang', targetLang);
      
      const currentPath = window.location.pathname;
      const search = window.location.search;
      const hash = window.location.hash;

      // Determine target destination
      if (targetLang === 'zh') {
        if (currentPath.endsWith('/en/') || currentPath.endsWith('/en/index.html')) {
          window.location.href = '../zh/' + search + hash;
        } else if (currentPath.endsWith('/zh/') || currentPath.endsWith('/zh/index.html')) {
          // already on zh
        } else {
          // root
          window.location.href = './zh/' + search + hash;
        }
      } else if (targetLang === 'en') {
        if (currentPath.endsWith('/zh/') || currentPath.endsWith('/zh/index.html')) {
          window.location.href = '../en/' + search + hash;
        } else if (currentPath.endsWith('/en/') || currentPath.endsWith('/en/index.html')) {
          // already on en
        } else {
          // root
          window.location.href = './en/' + search + hash;
        }
      }
    });
  });
}
