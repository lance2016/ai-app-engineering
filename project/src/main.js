import * as XLSX from "xlsx";

const icon = (name, size = 18) => {
  const paths = {
    sheet: '<path d="M5 3.5h9.5L19 8v12.5H5z"/><path d="M14 3.5V8h5"/><path d="M8 12h8M8 15.5h8"/>',
    upload: '<path d="M12 16V4"/><path d="m7.5 8.5 4.5-4.5 4.5 4.5"/><path d="M4 15.5v3h16v-3"/>',
    table: '<rect x="3.5" y="4" width="17" height="16" rx="2"/><path d="M3.5 9h17M3.5 14h17M9 4v16M15 4v16"/>',
    check: '<path d="m5 12 4.3 4.3L19.5 6"/>',
    columns: '<path d="M4 5h16M4 12h16M4 19h16"/><path d="M8 3v18M16 3v18"/>',
    filter: '<path d="M4 6h16M7 12h10M10 18h4"/>',
    search: '<circle cx="10.8" cy="10.8" r="6.3"/><path d="m16 16 4 4"/>',
    chevron: '<path d="m7 10 5 5 5-5"/>',
    close: '<path d="m6 6 12 12M18 6 6 18"/>',
    layers: '<path d="m12 3 8 4.3-8 4.2-8-4.2z"/><path d="m4 12 8 4.2 8-4.2M4 16.7l8 4.3 8-4.3"/>',
    pin: '<path d="m15.5 4.5 4 4-2.2 2.2-1.1-.2-3.7 3.7.2 1.1-2.2 2.2-4-4 2.2-2.2 1.1.2 3.7-3.7-.2-1.1z"/><path d="m9.5 14.5-5 5"/>',
    eye: '<path d="M2.7 12s3.2-5.1 9.3-5.1 9.3 5.1 9.3 5.1-3.2 5.1-9.3 5.1S2.7 12 2.7 12Z"/><circle cx="12" cy="12" r="2.2"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 10.6v5.2M12 7.6h.01"/>',
    trash: '<path d="M4.5 7h15M9 7V4.5h6V7M7 7l.7 13h8.6L17 7M10 10.5v6M14 10.5v6"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    arrow: '<path d="M4 12h15M13 6l6 6-6 6"/>',
    grid: '<rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/>',
  };
  return `<svg class="icon icon-${name}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.info}</svg>`;
};

const demoFiles = () => [
  {
    id: "demo-workbook",
    name: "3月人事汇总.xlsx",
    size: 18342,
    isDemo: true,
    sheets: [
      {
        id: "demo-roster",
        name: "名单总表",
        included: true,
        headerRow: 1,
        rows: [
          ["2026 年 3 月排班名单"],
          ["员工编号", "姓名", "部门", "手机号", "入职日期"],
          ["A-104", "林夏", "产品", "138 0013 0404", "2024-04-08"],
          ["B-204", "周宁", "销售", "138 0013 0204", "2023-11-02"],
          ["C-118", "苏禾", "客服", "138 0013 0118", "2025-01-13"],
          ["B-204", "周宁", "销售", "138 0013 0204", "2023-11-02"],
          ["D-032", "陈默", "研发", "138 0013 0032", "2022-09-19"],
          ["E-055", "许澄", "设计", "138 0013 0055", "2024-08-23"],
        ],
      },
      {
        id: "demo-support",
        name: "客服组",
        included: true,
        headerRow: 0,
        rows: [
          ["员工编号", "姓名", "部门", "手机号", "入职日期"],
          ["C-118", "苏禾", "客服", "138 0013 0118", "2025-01-13"],
          ["F-091", "顾言", "客服", "138 0013 0091", "2024-12-16"],
          ["G-012", "乔乔", "客服", "138 0013 0012", "2025-02-03"],
          ["C-118", "苏禾", "客服", "138 0013 0118", "2025-01-13"],
        ],
      },
    ],
  },
  {
    id: "demo-addendum",
    name: "入职补录.csv",
    size: 942,
    isDemo: true,
    sheets: [
      {
        id: "demo-addendum-sheet",
        name: "入职补录",
        included: true,
        headerRow: 0,
        rows: [
          ["员工编号", "姓名", "部门", "手机号", "入职日期"],
          ["B-204", "周宁", "销售", "138 0013 0204", "2023-11-02"],
          ["H-207", "魏然", "市场", "138 0013 0207", "2025-03-05"],
          ["I-033", "许墨", "运营", "138 0013 0033", "2024-07-11"],
        ],
      },
    ],
  },
];

const state = {
  files: demoFiles(),
  activeSheetId: "demo-roster",
  keyMode: "columns",
  selectedKeyColumns: ["员工编号"],
  trimWhitespace: true,
  caseSensitive: false,
  ignoreBlank: true,
  query: "",
  resultFilter: "all",
  sourceFilter: "all",
  markedOnly: false,
  marks: new Set(["demo-roster-1"]),
  selectedResult: null,
  toast: null,
  isDemo: true,
};

const app = document.querySelector("#app");
const fileInput = document.querySelector("#file-input");

const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

const formatSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
};

const allSheets = () => state.files.flatMap((file) => file.sheets.map((sheet) => ({ file, sheet })));
const activeSource = () => allSheets().find(({ sheet }) => sheet.id === state.activeSheetId) || allSheets()[0];

const normalizeCell = (value) => {
  let text = value == null ? "" : String(value);
  if (state.trimWhitespace) text = text.trim();
  if (!state.caseSensitive) text = text.toLocaleLowerCase("zh-CN");
  return text;
};

const normalizedSheet = (file, sheet) => {
  const rawHeader = sheet.rows[sheet.headerRow] || [];
  const headers = [];
  rawHeader.forEach((cell, index) => {
    const base = String(cell ?? "").trim() || `列 ${index + 1}`;
    const seen = headers.filter((header) => header === base || header.startsWith(`${base} (`)).length;
    headers.push(seen ? `${base} (${seen + 1})` : base);
  });
  const width = Math.max(headers.length, ...sheet.rows.map((row) => row.length), 1);
  while (headers.length < width) headers.push(`列 ${headers.length + 1}`);
  const rows = sheet.rows.slice(sheet.headerRow + 1).map((cells, index) => ({
    id: `${sheet.id}-${index}`,
    values: Array.from({ length: width }, (_, cellIndex) => cells[cellIndex] ?? ""),
    rowNumber: sheet.headerRow + index + 2,
    file,
    sheet,
    headers,
  }));
  return { headers, rows };
};

const availableColumns = () => {
  const names = [];
  allSheets().forEach(({ file, sheet }) => {
    if (!sheet.included) return;
    normalizedSheet(file, sheet).headers.forEach((header) => {
      if (!names.includes(header)) names.push(header);
    });
  });
  return names;
};

const ensureColumnSelection = () => {
  const columns = availableColumns();
  state.selectedKeyColumns = state.selectedKeyColumns.filter((column) => columns.includes(column));
  if (!state.selectedKeyColumns.length && columns.length) state.selectedKeyColumns = [columns[0]];
};

const buildResults = () => {
  ensureColumnSelection();
  const columns = availableColumns();
  const records = [];
  allSheets().forEach(({ file, sheet }) => {
    if (!sheet.included) return;
    const data = normalizedSheet(file, sheet);
    data.rows.forEach((row) => {
      const valuesByHeader = Object.fromEntries(data.headers.map((header, index) => [header, row.values[index] ?? ""]));
      const values = state.keyMode === "row"
        ? data.headers.map((header) => normalizeCell(valuesByHeader[header]))
        : state.selectedKeyColumns.map((header) => normalizeCell(valuesByHeader[header] ?? ""));
      const blank = values.every((value) => value === "");
      if (state.ignoreBlank && blank) return;
      const key = JSON.stringify(values);
      records.push({ ...row, file, sheet, data, valuesByHeader, key, displayKey: values.map((value) => value || "空白").join(" · "), columns });
    });
  });
  const groups = new Map();
  records.forEach((record) => {
    if (!groups.has(record.key)) groups.set(record.key, []);
    groups.get(record.key).push(record);
  });
  let groupIndex = 0;
  const duplicateGroups = [...groups.entries()].filter(([, rows]) => rows.length > 1).map(([key, rows]) => {
    groupIndex += 1;
    return { key, rows, groupId: `D${String(groupIndex).padStart(2, "0")}` };
  });
  const resultRows = duplicateGroups.flatMap((group) => group.rows.map((record, index) => ({
    ...record,
    groupId: group.groupId,
    groupSize: group.rows.length,
    occurrence: index + 1,
    marked: state.marks.has(record.id) || state.marks.has(group.key),
  })));
  return { records, duplicateGroups, resultRows, columns };
};

const currentAnalysis = () => buildResults();

const renderHeader = (analysis) => `
  <header class="topbar">
    <div class="brand-lockup">
      <div class="brand-mark">${icon("sheet", 22)}</div>
      <div>
        <div class="brand-name">表检 <span>Sheet Scout</span></div>
        <div class="brand-caption">给表格做一次安静的体检</div>
      </div>
    </div>
    <div class="topbar-right">
      <span class="privacy-chip"><span class="privacy-dot"></span>文件仅在本地处理</span>
      <span class="readonly-chip">只读模式</span>
    </div>
  </header>
  <div class="workspace-head">
    <div>
      <div class="eyebrow">重复校验 / Duplicate check</div>
      <h1>先把重复项找出来。</h1>
      <p class="lede">按文件、Sheet 和字段组合比对数据。原始文件不会被改动，也不会离开当前浏览器。</p>
    </div>
    <div class="head-summary">
      <div class="summary-label">当前范围</div>
      <div class="summary-value">${state.files.length} 个文件 <span>·</span> ${allSheets().filter(({ sheet }) => sheet.included).length} 个 Sheet</div>
      <button class="text-button" data-action="clear-files">清空并重新开始 ${icon("arrow", 15)}</button>
    </div>
  </div>
`;

const renderSidebar = () => `
  <aside class="sidebar">
    <div class="sidebar-section source-section">
      <div class="section-kicker">01 <span>数据来源</span></div>
      <div class="source-heading">
        <h2>选择要比对的表</h2>
        <span class="count-pill">${allSheets().filter(({ sheet }) => sheet.included).length}</span>
      </div>
      <div class="source-list">
        ${state.files.map((file) => `
          <div class="file-block">
            <div class="file-row">
              <span class="file-icon">${icon("sheet", 16)}</span>
              <div class="file-name" title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</div>
              <span class="file-size">${formatSize(file.size)}</span>
            </div>
            ${file.sheets.map((sheet) => `
              <button class="sheet-row ${sheet.id === state.activeSheetId ? "active" : ""}" data-action="select-sheet" data-sheet-id="${sheet.id}">
                <span class="sheet-branch"></span>
                <span class="sheet-name">${escapeHtml(sheet.name)}</span>
                <span class="sheet-check ${sheet.included ? "on" : ""}" data-action="toggle-sheet" data-sheet-id="${sheet.id}">${sheet.included ? icon("check", 13) : ""}</span>
              </button>
            `).join("")}
          </div>
        `).join("") || `<div class="empty-source">还没有导入文件<br /><span>支持 XLSX / XLS / CSV / TSV</span></div>`}
      </div>
      <button class="upload-more" data-action="open-file-picker">${icon("plus", 16)} 加入文件</button>
    </div>
    <div class="sidebar-rule"></div>
    <div class="sidebar-section rule-section">
      <div class="section-kicker">02 <span>查重规则</span></div>
      <h2>重复由什么决定？</h2>
      <div class="rule-card">
        <div class="rule-label">比对方式</div>
        <div class="segmented">
          <button class="segment ${state.keyMode === "columns" ? "selected" : ""}" data-action="set-key-mode" data-mode="columns">字段组合</button>
          <button class="segment ${state.keyMode === "row" ? "selected" : ""}" data-action="set-key-mode" data-mode="row">整行一致</button>
        </div>
        <div class="rule-label key-label">查重字段</div>
        <div class="column-options ${state.keyMode === "row" ? "muted" : ""}">
          ${availableColumns().slice(0, 9).map((column) => `
            <label class="check-option">
              <input type="checkbox" data-action="toggle-column" data-column="${escapeHtml(column)}" ${state.selectedKeyColumns.includes(column) ? "checked" : ""} ${state.keyMode === "row" ? "disabled" : ""} />
              <span class="fake-checkbox">${state.selectedKeyColumns.includes(column) ? icon("check", 12) : ""}</span>
              <span>${escapeHtml(column)}</span>
            </label>
          `).join("") || `<div class="empty-mini">导入表格后选择字段</div>`}
          ${availableColumns().length > 9 ? `<div class="more-columns">还有 ${availableColumns().length - 9} 个字段</div>` : ""}
        </div>
        <div class="toggle-list">
          <label class="toggle-row"><span>忽略前后空格</span><input type="checkbox" data-action="toggle-option" data-option="trimWhitespace" ${state.trimWhitespace ? "checked" : ""}/><span class="switch"></span></label>
          <label class="toggle-row"><span>区分大小写</span><input type="checkbox" data-action="toggle-option" data-option="caseSensitive" ${state.caseSensitive ? "checked" : ""}/><span class="switch"></span></label>
          <label class="toggle-row"><span>忽略空白键值</span><input type="checkbox" data-action="toggle-option" data-option="ignoreBlank" ${state.ignoreBlank ? "checked" : ""}/><span class="switch"></span></label>
        </div>
      </div>
    </div>
    <div class="sidebar-footnote">
      ${icon("info", 15)} <span>任何筛选、标记和表头选择都只作用于当前查看，不会写回源文件。</span>
    </div>
  </aside>
`;

const renderHeaderPicker = () => {
  const source = activeSource();
  if (!source) return "";
  const { file, sheet } = source;
  const previewRows = sheet.rows.slice(0, Math.min(sheet.rows.length, 7));
  const maxWidth = Math.max(1, ...previewRows.map((row) => row.length));
  return `
    <section class="panel header-panel">
      <div class="panel-title-row">
        <div>
          <div class="panel-kicker">表头设置 · ${escapeHtml(file.name)} / ${escapeHtml(sheet.name)}</div>
          <h2>哪一行是表头？</h2>
        </div>
        <div class="row-select-note">点击行号即可切换 <span>${icon("table", 14)}</span></div>
      </div>
      <p class="panel-description">有些文件前面会带标题、说明或日期。选中真正的字段名那一行，下面的查重字段会跟着更新。</p>
      <div class="raw-preview-wrap">
        <table class="raw-preview">
          <thead><tr><th class="row-number-head">行</th>${Array.from({ length: Math.min(maxWidth, 6) }, (_, index) => `<th>${String.fromCharCode(65 + index)}</th>`).join("")}</tr></thead>
          <tbody>
            ${previewRows.map((row, index) => `
              <tr class="${index === sheet.headerRow ? "header-selected" : ""}">
                <td class="row-number"><button data-action="set-header-row" data-row-index="${index}" data-sheet-id="${sheet.id}" aria-label="选择第 ${index + 1} 行为表头">${index + 1}</button></td>
                ${Array.from({ length: Math.min(maxWidth, 6) }, (_, cellIndex) => `<td>${escapeHtml(row[cellIndex] ?? "")}</td>`).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
      <div class="header-status"><span class="status-mark">${icon("check", 14)}</span> 当前使用第 ${sheet.headerRow + 1} 行作为表头，共识别 ${normalizedSheet(file, sheet).headers.length} 个字段</div>
    </section>
  `;
};

const renderStat = (number, label, detail, accent = "") => `<div class="stat-card ${accent}"><div class="stat-number">${number}</div><div class="stat-label">${label}</div><div class="stat-detail">${detail}</div></div>`;

const visibleResults = (analysis) => analysis.resultRows.filter((row) => {
  if (state.resultFilter === "marked" && !row.marked) return false;
  if (state.sourceFilter !== "all" && row.file.id !== state.sourceFilter) return false;
  if (state.query) {
    const haystack = [row.file.name, row.sheet.name, row.groupId, row.displayKey, row.rowNumber, ...Object.values(row.valuesByHeader)].join(" ").toLocaleLowerCase("zh-CN");
    if (!haystack.includes(state.query.toLocaleLowerCase("zh-CN"))) return false;
  }
  return true;
});

const renderResultTable = (analysis) => {
  const rows = visibleResults(analysis);
  if (!analysis.records.length) {
    return `<div class="no-duplicates empty-results"><div class="success-icon neutral">${icon("upload", 25)}</div><h3>先导入一份表格</h3><p>拖入一个或多个 Excel、CSV 文件，开始选择表头并查找重复项。</p><button class="small-button" data-action="open-file-picker">选择文件 ${icon("arrow", 14)}</button></div>`;
  }
  if (!analysis.resultRows.length) {
    return `<div class="no-duplicates"><div class="success-icon">${icon("check", 28)}</div><h3>没有发现重复项</h3><p>当前范围内的 ${analysis.records.length} 行数据，没有符合规则的重复键值。</p></div>`;
  }
  if (!rows.length) {
    return `<div class="no-duplicates filtered-empty"><div class="success-icon neutral">${icon("filter", 25)}</div><h3>这个筛选没有结果</h3><p>换一个关键词或清除筛选条件试试。</p><button class="small-button" data-action="reset-filters">清除筛选</button></div>`;
  }
  return `
    <div class="table-scroll">
      <table class="results-table">
        <thead><tr><th class="mark-column"></th><th>组别</th><th>命中字段</th><th>来源</th><th>Sheet</th><th>行</th><th>出现次数</th><th>查看</th></tr></thead>
        <tbody>
          ${rows.map((row) => `
            <tr class="result-row ${state.selectedResult?.id === row.id ? "selected" : ""}" data-action="select-result" data-row-id="${row.id}">
              <td class="mark-column"><button class="mark-button ${row.marked ? "marked" : ""}" data-action="toggle-mark" data-mark-id="${row.id}" aria-label="${row.marked ? "取消标记" : "标记"}">${icon("pin", 15)}</button></td>
              <td><span class="group-badge">${row.groupId}</span></td>
              <td><span class="key-value">${escapeHtml(row.displayKey)}</span></td>
              <td class="source-cell"><span class="file-dot"></span>${escapeHtml(row.file.name)}</td>
              <td>${escapeHtml(row.sheet.name)}</td>
              <td class="row-cell">${row.rowNumber}</td>
              <td><span class="occurrence">${row.groupSize} 次</span></td>
              <td class="view-cell">${icon("eye", 16)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
    <div class="table-foot"><span>显示 ${rows.length} 行重复记录</span><span>数据顺序保持与源文件一致</span></div>
  `;
};

const renderResults = (analysis) => `
  <section class="results-section">
    <div class="results-heading">
      <div>
        <div class="panel-kicker">结果概览 · ${new Date().toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" })}</div>
        <h2>重复记录</h2>
      </div>
      <div class="result-actions"><span class="analysis-time">刚刚完成</span><button class="icon-button" title="查看字段规则" data-action="scroll-rules">${icon("info", 17)}</button></div>
    </div>
    <div class="stats-grid">
      ${renderStat(analysis.records.length, "已扫描行数", `${allSheets().filter(({ sheet }) => sheet.included).length} 个 Sheet`)}
      ${renderStat(analysis.duplicateGroups.length, "重复组", analysis.duplicateGroups.length ? `共涉及 ${analysis.resultRows.length} 行` : "当前范围无重复")}
      ${renderStat(analysis.resultRows.length, "重复记录", analysis.resultRows.length ? "同一键值出现 2 次以上" : "可以继续下一步")}
      ${renderStat(new Set(analysis.resultRows.map((row) => row.file.id)).size, "涉及文件", "跨文件自动归组", "accent-stat")}
    </div>
    <div class="result-toolbar">
      <div class="filter-tabs">
        <button class="filter-tab ${state.resultFilter === "all" ? "active" : ""}" data-action="set-result-filter" data-filter="all">全部 <span>${analysis.resultRows.length}</span></button>
        <button class="filter-tab ${state.resultFilter === "marked" ? "active" : ""}" data-action="set-result-filter" data-filter="marked">已标记 <span>${analysis.resultRows.filter((row) => row.marked).length}</span></button>
      </div>
      <div class="toolbar-controls">
        <label class="search-control">${icon("search", 16)}<input type="search" placeholder="搜索姓名、字段值或来源" value="${escapeHtml(state.query)}" data-action="search" /></label>
        <label class="select-control">${icon("filter", 15)}<select data-action="source-filter"><option value="all">所有来源</option>${state.files.map((file) => `<option value="${file.id}" ${state.sourceFilter === file.id ? "selected" : ""}>${escapeHtml(file.name)}</option>`).join("")}</select>${icon("chevron", 14)}</label>
      </div>
    </div>
    <div class="results-panel">${renderResultTable(analysis)}</div>
  </section>
`;

const renderDetail = (analysis) => {
  if (!state.selectedResult) return `
    <aside class="detail-panel empty-detail">
      <div class="detail-placeholder-icon">${icon("layers", 24)}</div>
      <h3>选择一条记录</h3>
      <p>点击结果表中的任意一行，在这里查看它来自哪个文件、哪一个 Sheet，以及完整的原始字段。</p>
    </aside>
  `;
  const row = analysis.resultRows.find((item) => item.id === state.selectedResult.id) || analysis.resultRows[0];
  if (!row) return "";
  return `
    <aside class="detail-panel">
      <div class="detail-topline"><span class="detail-kicker">重复组 ${row.groupId}</span><button class="close-detail" data-action="close-detail" aria-label="关闭详情">${icon("close", 16)}</button></div>
      <div class="detail-title-row"><h3>${escapeHtml(row.displayKey)}</h3><button class="mark-button ${row.marked ? "marked" : ""}" data-action="toggle-mark" data-mark-id="${row.id}" aria-label="标记当前记录">${icon("pin", 15)}</button></div>
      <p class="detail-summary">这组键值在当前范围出现 <strong>${row.groupSize} 次</strong>。当前查看第 ${row.occurrence} 条。</p>
      <div class="detail-meta"><div><span>来源文件</span><strong>${escapeHtml(row.file.name)}</strong></div><div><span>工作表</span><strong>${escapeHtml(row.sheet.name)}</strong></div><div><span>源文件行</span><strong>第 ${row.rowNumber} 行</strong></div></div>
      <div class="detail-divider"></div>
      <div class="detail-label">原始字段</div>
      <div class="detail-fields">${row.data.headers.map((header, index) => `<div class="detail-field"><span>${escapeHtml(header)}</span><strong>${escapeHtml(row.valuesByHeader[header] || "—")}</strong></div>`).join("")}</div>
      <div class="detail-readonly">${icon("eye", 14)} 仅查看，不会修改源文件</div>
    </aside>
  `;
};

const renderApp = () => {
  const analysis = currentAnalysis();
  app.innerHTML = `
    ${renderHeader(analysis)}
    <main class="app-shell">
      ${renderSidebar()}
      <div class="main-column">
        ${renderHeaderPicker()}
        ${renderResults(analysis)}
      </div>
      ${renderDetail(analysis)}
    </main>
    <footer class="app-footer"><span>${icon("check", 14)} 只读查看 · 原文件不改 · 结果随设置即时更新</span><span>支持 XLSX / XLS / CSV / TSV</span></footer>
    ${state.toast ? `<div class="toast">${icon("check", 15)} ${escapeHtml(state.toast)}</div>` : ""}
  `;
};

const setToast = (message) => {
  state.toast = message;
  renderApp();
  window.setTimeout(() => {
    state.toast = null;
    renderApp();
  }, 2200);
};

const parseDelimited = (text, delimiter) => {
  const rows = [];
  let row = [];
  let cell = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (char === '"') {
      if (quoted && next === '"') { cell += '"'; index += 1; }
      else quoted = !quoted;
    } else if (char === delimiter && !quoted) {
      row.push(cell); cell = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") index += 1;
      row.push(cell); cell = "";
      if (row.some((value) => value !== "") || rows.length) rows.push(row);
      row = [];
    } else {
      cell += char;
    }
  }
  if (cell !== "" || row.length) { row.push(cell); rows.push(row); }
  return rows;
};

const parseFile = async (file) => {
  const lowerName = file.name.toLocaleLowerCase("zh-CN");
  const fileId = `file-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  if (lowerName.endsWith(".csv") || lowerName.endsWith(".tsv")) {
    const text = new TextDecoder("utf-8").decode(await file.arrayBuffer()).replace(/^\uFEFF/, "");
    const delimiter = lowerName.endsWith(".tsv") || (text.split("\n")[0].includes("\t") && !text.split("\n")[0].includes(",")) ? "\t" : ",";
    return { id: fileId, name: file.name, size: file.size, sheets: [{ id: `${fileId}-sheet`, name: file.name.replace(/\.[^/.]+$/, ""), included: true, headerRow: 0, rows: parseDelimited(text, delimiter) }] };
  }
  const workbook = XLSX.read(await file.arrayBuffer(), { type: "array", cellDates: true, raw: false });
  return { id: fileId, name: file.name, size: file.size, sheets: workbook.SheetNames.map((name, index) => ({ id: `${fileId}-sheet-${index}`, name, included: true, headerRow: 0, rows: XLSX.utils.sheet_to_json(workbook.Sheets[name], { header: 1, defval: "", raw: false }) })) };
};

const loadFiles = async (files) => {
  const parsed = await Promise.all([...files].map(parseFile));
  state.files = [...state.files.filter((file) => !file.isDemo), ...parsed];
  state.isDemo = false;
  state.activeSheetId = parsed[0]?.sheets[0]?.id || state.activeSheetId;
  state.selectedResult = null;
  state.marks = new Set();
  ensureColumnSelection();
  setToast(`已加入 ${parsed.length} 个文件`);
};

const demoReset = () => {
  state.files = demoFiles();
  state.activeSheetId = "demo-roster";
  state.keyMode = "columns";
  state.selectedKeyColumns = ["员工编号"];
  state.trimWhitespace = true;
  state.caseSensitive = false;
  state.ignoreBlank = true;
  state.query = "";
  state.resultFilter = "all";
  state.sourceFilter = "all";
  state.selectedResult = null;
  state.marks = new Set(["demo-roster-1"]);
  state.isDemo = true;
  renderApp();
};

document.addEventListener("click", (event) => {
  const target = event.target.closest("[data-action]");
  if (!target) return;
  const action = target.dataset.action;
  if (action === "open-file-picker") fileInput.click();
  if (action === "clear-files") { state.files = []; state.activeSheetId = null; state.selectedResult = null; state.marks.clear(); renderApp(); }
  if (action === "select-sheet") { state.activeSheetId = target.dataset.sheetId; renderApp(); }
  if (action === "toggle-sheet") { event.stopPropagation(); const source = allSheets().find(({ sheet }) => sheet.id === target.dataset.sheetId); if (source) { source.sheet.included = !source.sheet.included; state.selectedResult = null; renderApp(); } }
  if (action === "set-key-mode") { state.keyMode = target.dataset.mode; renderApp(); }
  if (action === "set-header-row") { const source = allSheets().find(({ sheet }) => sheet.id === target.dataset.sheetId); if (source) { source.sheet.headerRow = Number(target.dataset.rowIndex); state.selectedResult = null; ensureColumnSelection(); renderApp(); } }
  if (action === "set-result-filter") { state.resultFilter = target.dataset.filter; renderApp(); }
  if (action === "source-filter") return;
  if (action === "reset-filters") { state.query = ""; state.resultFilter = "all"; state.sourceFilter = "all"; renderApp(); }
  if (action === "select-result") { const row = currentAnalysis().resultRows.find((item) => item.id === target.dataset.rowId); if (row) { state.selectedResult = row; renderApp(); } }
  if (action === "close-detail") { state.selectedResult = null; renderApp(); }
  if (action === "toggle-mark") { event.stopPropagation(); const id = target.dataset.markId; if (state.marks.has(id)) state.marks.delete(id); else state.marks.add(id); renderApp(); }
  if (action === "scroll-rules") document.querySelector(".rule-section")?.scrollIntoView({ behavior: "smooth", block: "center" });
});

document.addEventListener("change", (event) => {
  const target = event.target;
  const action = target.dataset.action;
  if (action === "toggle-column") { if (target.checked) state.selectedKeyColumns.push(target.dataset.column); else state.selectedKeyColumns = state.selectedKeyColumns.filter((column) => column !== target.dataset.column); renderApp(); }
  if (action === "toggle-option") { state[target.dataset.option] = target.checked; renderApp(); }
  if (action === "source-filter") { state.sourceFilter = target.value; renderApp(); }
});

document.addEventListener("input", (event) => {
  if (event.target.dataset.action !== "search") return;
  state.query = event.target.value;
  const caret = event.target.selectionStart;
  renderApp();
  const input = document.querySelector('[data-action="search"]');
  input?.focus();
  input?.setSelectionRange(caret, caret);
});

fileInput.addEventListener("change", () => {
  if (fileInput.files?.length) loadFiles(fileInput.files).catch((error) => setToast(`文件读取失败：${error.message}`));
  fileInput.value = "";
});

document.addEventListener("dragover", (event) => { if (event.target.closest(".main-column, .sidebar")) event.preventDefault(); });
document.addEventListener("drop", (event) => {
  if (!event.target.closest(".main-column, .sidebar")) return;
  event.preventDefault();
  if (event.dataTransfer.files?.length) loadFiles(event.dataTransfer.files).catch((error) => setToast(`文件读取失败：${error.message}`));
});

renderApp();
