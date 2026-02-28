// @ts-check

(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const sum = (values) => values.reduce((acc, value) => acc + value, 0);

  /** @type {{generatedAt: string, tableImpact: Array<{table: string, script_count: number}>, scripts: Array<any>} | undefined} */
  const demoData = window.DEMO_DATA;
  /** @type {{byFile?: Record<string, {script_id:number, mssql:string, mysql:string}>, byId?: Record<string, {script_file:string, mssql:string, mysql:string}>} | undefined} */
  const scriptSqlData = window.SCRIPT_SQL_DATA;

  if (!demoData?.scripts?.length) {
    document.body.innerHTML = "<p style='padding:2rem;font-family:sans-serif'>Demo data missing: load demo-data.js first.</p>";
    return;
  }

  const scripts = demoData.scripts.map((script) => {
    const tables = script.tables ? String(script.tables).split("|").filter(Boolean) : [];
    return {
      ...script,
      tables,
      primaryTable: tables[0] ?? "Unknown",
      runtimeSec: script.total_duration_ms / 1000,
    };
  });

  const summary = buildSummary(scripts);
  const openScriptModal = setupScriptModal(scripts, scriptSqlData);

  renderHeader(summary);
  renderAct1Context(scripts, summary);
  setupWorkloadMap(scripts, summary, demoData.tableImpact, openScriptModal);
  setupProcessCards(summary);
  setupExamplePanel(scripts, scriptSqlData);
  setupSimulator(summary);

  const generatedAt = $("#generated-at");
  if (generatedAt) {
    generatedAt.textContent = new Date(demoData.generatedAt).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      timeZone: "UTC",
    });
  }

  /**
   * @param {Array<any>} rows
   */
  function buildSummary(rows) {
    const runtimeMsList = rows.map((row) => Number(row.total_duration_ms) || 0);
    const totalRuntimeMs = sum(runtimeMsList);
    const sortedByRuntime = [...rows].sort((a, b) => b.total_duration_ms - a.total_duration_ms);
    const top10RuntimeMs = sum(sortedByRuntime.slice(0, 10).map((row) => row.total_duration_ms));
    const manualReviewCount = rows.filter((row) => row.needs_manual_review).length;
    const firstPassCount = rows.filter((row) => Number(row.conversion_attempts) === 1).length;
    const finalPassCount = rows.filter((row) => ["passed", "passed_with_notes"].includes(String(row.final_status))).length;
    const avgAttempts = sum(rows.map((row) => Number(row.conversion_attempts) || 0)) / rows.length;
    const avgComplexity = sum(rows.map((row) => Number(row.complexity) || 0)) / rows.length;
    const totalExecutions = sum(rows.map((row) => Number(row.executions) || 0));
    const runtimePerScriptSec = totalRuntimeMs / 1000 / rows.length;

    const runtimeByCategoryMap = rows.reduce((acc, row) => {
      const key = row.category ?? "unknown";
      acc[key] = (acc[key] ?? 0) + (Number(row.total_duration_ms) || 0);
      return acc;
    }, /** @type {Record<string, number>} */ ({}));

    const runtimeByCategory = Object.entries(runtimeByCategoryMap)
      .map(([category, runtimeMs]) => ({
        category,
        runtimeMs,
        runtimePct: totalRuntimeMs === 0 ? 0 : (runtimeMs * 100) / totalRuntimeMs,
      }))
      .sort((a, b) => b.runtimeMs - a.runtimeMs);

    return {
      scriptCount: rows.length,
      manualReviewRate: (manualReviewCount * 100) / rows.length,
      firstPassRate: (firstPassCount * 100) / rows.length,
      finalPassRate: (finalPassCount * 100) / rows.length,
      avgAttempts,
      avgComplexity,
      totalRuntimeMs,
      totalExecutions,
      runtimePerScriptSec,
      top10RuntimePct: totalRuntimeMs === 0 ? 0 : (top10RuntimeMs * 100) / totalRuntimeMs,
      runtimeByCategory,
      sortedByRuntime,
    };
  }

  /**
   * @param {ReturnType<typeof buildSummary>} stats
   */
  function renderHeader(stats) {
    setText("#metric-script-count", String(stats.scriptCount));
    setText("#metric-runtime-share", `${stats.top10RuntimePct.toFixed(0)}%`);
    setText("#metric-manual-rate", `${stats.manualReviewRate.toFixed(0)}%`);
    setText("#metric-first-pass", `${stats.firstPassRate.toFixed(0)}%`);
  }

  /**
   * @param {Array<any>} rows
   * @param {ReturnType<typeof buildSummary>} stats
   */
  function renderAct1Context(rows, stats) {
    const datasetInput = $("#dataset-input");
    const challengeSignals = $("#challenge-signals");

    if (datasetInput) {
      const attemptCount = Math.round(sum(rows.map((row) => Number(row.conversion_attempts) || 0)));
      datasetInput.textContent =
        `Synthetic migration pack with 100 MSSQL scripts and 100 MySQL outputs, paired schema files, manifest metadata, ` +
        `${stats.totalExecutions.toLocaleString("en-US")} observed executions, and ${attemptCount} conversion attempts logged.`;
    }

    if (challengeSignals) {
      const countTag = (tag) => rows.filter((row) => String(row.tags || "").split("|").includes(tag)).length;
      const openJsonCount = countTag("OPENJSON");
      const mergeCount = countTag("MERGE");
      const pivotCount = countTag("PIVOT");
      const nolockCount = countTag("NOLOCK");
      const crossApplyCount = countTag("CROSS APPLY");

      challengeSignals.innerHTML = [
        `Preserving numeric precision and JSON path typing in OPENJSON -> JSON_TABLE rewrites (${openJsonCount} scripts).`,
        `MySQL has no direct MERGE equivalent; correctness depends on unique-key design (${mergeCount} scripts).`,
        `PIVOT becomes conditional aggregation, which can change performance and indexing behavior (${pivotCount} scripts).`,
        `Removing NOLOCK and CROSS APPLY patterns requires explicit isolation and normalization choices (${nolockCount + crossApplyCount} scripts).`,
      ]
        .map((item) => `<li>${escapeHtml(item)}</li>`)
        .join("");
    }
  }

  /**
   * @param {"category"|"table"|"risk"|"workload"} mode
   * @param {Array<any>} rows
   * @param {Array<string>} topTables
   * @param {ReturnType<typeof buildSummary>} stats
   */
  function renderModeContext(mode, rows, topTables, stats) {
    const titleEl = $("#query-bars-title");
    const listEl = $("#query-bars-list");
    const hotspotEl = $("#hotspot-signal");
    if (!titleEl || !listEl || !hotspotEl) {
      return;
    }

    const totalQueries = Math.max(1, sum(rows.map((row) => Number(row.executions) || 0)));
    const totalRuntime = Math.max(1, sum(rows.map((row) => Number(row.total_duration_ms) || 0)));

    /**
     * @param {(row: any) => string} groupFn
     */
    const aggregate = (groupFn) => {
      const grouped = new Map();
      rows.forEach((row) => {
        const key = groupFn(row);
        const prev = grouped.get(key) ?? { label: key, queries: 0, runtimeMs: 0, scripts: 0 };
        prev.queries += Number(row.executions) || 0;
        prev.runtimeMs += Number(row.total_duration_ms) || 0;
        prev.scripts += 1;
        grouped.set(key, prev);
      });
      return Array.from(grouped.values());
    };

    const pct = (value, total) => ((value * 100) / total).toFixed(1);
    const queryText = (value) => Number(value).toLocaleString("en-US");

    /** @type {Array<{label:string,queries:number,runtimeMs:number,scripts:number}>} */
    let entries = [];
    let heading = "Queries by purpose";
    let hotspot = "";

    if (mode === "category") {
      heading = "Queries by purpose";
      entries = aggregate((row) => titleCase(row.category)).sort((a, b) => b.queries - a.queries);
      const topByQueries = entries[0];
      const topByRuntime = [...entries].sort((a, b) => b.runtimeMs - a.runtimeMs)[0];
      if (topByQueries && topByRuntime) {
        hotspot =
          `${topByQueries.label} handles ${queryText(topByQueries.queries)} observed queries ` +
          `(${pct(topByQueries.queries, totalQueries)}%), while ${topByRuntime.label} carries ` +
          `${pct(topByRuntime.runtimeMs, totalRuntime)}% of runtime.`;
      }
    }

    if (mode === "table") {
      heading = "Queries by table family";
      entries = aggregate((row) => (topTables.includes(row.primaryTable) ? row.primaryTable : "Other")).sort(
        (a, b) => b.queries - a.queries
      );
      const top = entries[0];
      if (top) {
        hotspot =
          `${top.label} is the busiest table family with ${queryText(top.queries)} queries ` +
          `(${pct(top.queries, totalQueries)}%) and ${pct(top.runtimeMs, totalRuntime)}% of runtime load.`;
      }
    }

    if (mode === "risk") {
      heading = "Queries by migration risk";
      entries = aggregate((row) => (row.needs_manual_review ? "Manual review lane" : "Auto-convert lane")).sort(
        (a, b) => b.queries - a.queries
      );
      const manual = entries.find((entry) => entry.label === "Manual review lane");
      if (manual) {
        hotspot =
          `Manual-review scripts are ${manual.scripts} of ${rows.length}, but still drive ` +
          `${queryText(manual.queries)} queries and ${pct(manual.runtimeMs, totalRuntime)}% of runtime.`;
      }
    }

    if (mode === "workload") {
      heading = "Queries by frequency x complexity";
      const executionThreshold = Math.max(50, Math.round(stats.totalExecutions / rows.length));
      entries = aggregate((row) => {
        const highFreq = Number(row.executions) >= executionThreshold;
        const highComplexity = Number(row.complexity) >= 7;
        if (highFreq && highComplexity) return "High freq + High complexity";
        if (highFreq) return "High freq + Lower complexity";
        if (highComplexity) return "Lower freq + High complexity";
        return "Lower freq + Lower complexity";
      }).sort((a, b) => b.queries - a.queries);

      const busiest = entries[0];
      const costliest = [...entries].sort((a, b) => b.runtimeMs - a.runtimeMs)[0];
      if (busiest && costliest) {
        hotspot =
          `${busiest.label} is the busiest zone by query count (${queryText(busiest.queries)}), ` +
          `while ${costliest.label} accounts for the highest runtime burden (${pct(costliest.runtimeMs, totalRuntime)}%).`;
      }
    }

    titleEl.textContent = heading;
    listEl.innerHTML = entries
      .map((entry) => {
        const share = pct(entry.queries, totalQueries);
        return `
          <div class="bar-row">
            <div class="bar-label"><span>${escapeHtml(entry.label)}</span><span>${queryText(entry.queries)} · ${share}%</span></div>
            <div class="bar-track"><div class="bar-fill" style="width:${share}%"></div></div>
          </div>
        `;
      })
      .join("");
    hotspotEl.textContent = hotspot || "Hotspot signal updates with the selected grouping mode.";
  }

  /**
   * @param {Array<any>} rows
   * @param {{byFile?: Record<string, {script_id:number, mssql:string, mysql:string}>} | undefined} sqlStore
   */
  function setupScriptModal(rows, sqlStore) {
    const dialog = /** @type {HTMLDialogElement | null} */ ($("#script-modal"));
    const title = $("#modal-title");
    const subtitle = $("#modal-subtitle");
    const meta = $("#modal-meta");
    const source = $("#modal-source-code");
    const target = $("#modal-target-code");
    const diff = $("#modal-diff-view");

    if (!dialog || !title || !subtitle || !meta || !source || !target || !diff) {
      return () => {};
    }

    const byFile = new Map(rows.map((row) => [row.script_file, row]));

    dialog.addEventListener("click", (event) => {
      const rect = dialog.getBoundingClientRect();
      const clickedOutside =
        event.clientX < rect.left ||
        event.clientX > rect.right ||
        event.clientY < rect.top ||
        event.clientY > rect.bottom;
      if (clickedOutside) {
        dialog.close();
      }
    });

    /**
     * @param {any} input
     */
    return (input) => {
      const row = typeof input === "string" ? byFile.get(input) : input;
      if (!row) {
        return;
      }

      const sqlPair = sqlStore?.byFile?.[row.script_file];
      const sourceSql = sqlPair?.mssql ?? "-- Source SQL unavailable";
      const targetSql = sqlPair?.mysql ?? "-- Converted SQL unavailable";

      const riskLabel = row.needs_manual_review ? "High-touch" : row.complexity >= 7 ? "Elevated" : "Low-touch";
      const statusLabel = String(row.final_status || "unknown").replace(/_/g, " ");
      const tags = String(row.tags || "").split("|").filter(Boolean).join(", ");
      const tables = row.tables.length ? row.tables.join(", ") : "Unknown";

      title.textContent = row.script_file;
      subtitle.textContent = `${row.title} · Click-through conversion evidence`;

      meta.innerHTML = [
        ["Purpose", titleCase(row.category)],
        ["Complexity", `${row.complexity}/10`],
        ["Risk lane", riskLabel],
        ["Table family", tables],
        ["Executions", Number(row.executions).toLocaleString("en-US")],
        ["Runtime", `${row.runtimeSec.toFixed(2)} sec total`],
        ["Conversion", `${row.conversion_attempts} attempts · ${statusLabel}`],
        ["Model / warning", row.final_warnings ? `${row.final_model} · ${row.final_warnings}` : row.final_model ?? "n/a"],
        ["Tags", tags || "n/a"],
      ]
        .map(
          ([label, value]) => `
          <article class="meta-item">
            <h5>${escapeHtml(label)}</h5>
            <p>${escapeHtml(value)}</p>
          </article>
        `
        )
        .join("");

      source.innerHTML = renderSqlBlockFromText(sourceSql, "modal-source-block");
      target.innerHTML = renderSqlBlockFromText(targetSql, "modal-target-block");

      const diffCols = buildSideBySideDiff(sourceSql, targetSql);
      diff.innerHTML = `
        <div class="diff-grid">
          <section class="code-panel">
            <h4>Source (MSSQL)</h4>
            ${renderSqlBlockFromPrepared(diffCols.left, "modal-diff-source")}
          </section>
          <section class="code-panel">
            <h4>Target (MySQL)</h4>
            ${renderSqlBlockFromPrepared(diffCols.right, "modal-diff-target")}
          </section>
        </div>
      `;

      if (!dialog.open) {
        dialog.showModal();
      }
    };
  }

  /**
   * @param {Array<any>} rows
   * @param {ReturnType<typeof buildSummary>} stats
   * @param {Array<{table: string, script_count: number}>} tableImpact
   * @param {(row: any) => void} onNodeOpen
   */
  function setupWorkloadMap(rows, stats, tableImpact, onNodeOpen) {
    const canvas = /** @type {HTMLCanvasElement | null} */ ($("#sand-canvas"));
    const labelsRoot = $("#map-cluster-labels");
    const tooltip = $("#node-tooltip");
    const modeCaption = $("#mode-caption");
    const modeInsight = $("#mode-insight");

    if (!canvas || !labelsRoot || !tooltip || !modeCaption || !modeInsight) {
      return;
    }

    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) {
      return;
    }

    const categoryColor = {
      query: "#78d9ee",
      report: "#ff9f5a",
      etl: "#f2c55d",
      analytics: "#95f0b7",
      maintenance: "#d8a6ff",
      procedure: "#8fb1ff",
      view: "#ffde7f",
    };

    const modeMeta = {
      category: {
        caption:
          "Scripts separate into operational intent. Report and query workloads dominate, while ETL and analytics are smaller but denser.",
        insight:
          `Top 10 scripts consume ${stats.top10RuntimePct.toFixed(1)}% of runtime, so portfolio shape matters more than script count.`,
      },
      table: {
        caption:
          "When grouped by primary table, Orders and Product-adjacent flows absorb attention. These groups usually dictate cutover order.",
        insight:
          "Tables touched by many scripts are migration blast-radius multipliers. Change one index, feel it everywhere.",
      },
      risk: {
        caption:
          "Risk grouping separates scripts that can usually pass in one shot from those demanding semantic redesign and test scaffolding.",
        insight:
          `Manual-review scripts are ${stats.manualReviewRate.toFixed(0)}% of the portfolio, but they drive most migration uncertainty.`,
      },
      workload: {
        caption:
          "Frequency and complexity together reveal where business impact concentrates: high-run and high-complexity scripts are first to harden.",
        insight:
          "The upper-right zone is where regressions become incidents. That is where verification depth should be highest.",
      },
    };

    const topTables = tableImpact.slice(0, 6).map((entry) => entry.table);

    let mode = "category";
    const state = {
      width: 0,
      height: 0,
      dpr: 1,
      pointerX: -1000,
      pointerY: -1000,
      hoverId: -1,
    };

    const nodes = rows.map((row, index) => {
      const radius = clamp(2.4 + Math.sqrt(row.runtimeSec) * 0.5, 2.4, 9.5);
      return {
        index,
        row,
        x: 0,
        y: 0,
        tx: 0,
        ty: 0,
        vx: 0,
        vy: 0,
        radius,
        group: "",
      };
    });

    function resize() {
      const rect = canvas.getBoundingClientRect();
      state.width = rect.width;
      state.height = rect.height;
      state.dpr = window.devicePixelRatio || 1;
      canvas.width = Math.floor(state.width * state.dpr);
      canvas.height = Math.floor(state.height * state.dpr);
      ctx.setTransform(state.dpr, 0, 0, state.dpr, 0, 0);

      nodes.forEach((node) => {
        if (node.x === 0 && node.y === 0) {
          node.x = Math.random() * state.width;
          node.y = Math.random() * state.height;
        }
      });

      applyMode(mode);
    }

    /**
     * @param {string} selectedMode
     */
    function applyMode(selectedMode) {
      mode = selectedMode;
      const labels = [];

      if (mode === "category") {
        const groups = Array.from(new Set(rows.map((row) => row.category))).sort();
        const centers = spreadCenters(groups, state.width, state.height, 3);
        nodes.forEach((node) => {
          const key = node.row.category;
          const center = centers.get(key);
          if (!center) {
            return;
          }
          node.group = key;
          node.tx = center.x + randomJitter(44);
          node.ty = center.y + randomJitter(34);
        });
        groups.forEach((group) => {
          const center = centers.get(group);
          if (!center) {
            return;
          }
          labels.push({ text: titleCase(group), x: center.x, y: center.y - 52 });
        });
      }

      if (mode === "table") {
        const groups = [...topTables, "Other"];
        const centers = spreadCenters(groups, state.width, state.height, 3);
        nodes.forEach((node) => {
          const primary = topTables.includes(node.row.primaryTable) ? node.row.primaryTable : "Other";
          const center = centers.get(primary);
          if (!center) {
            return;
          }
          node.group = primary;
          node.tx = center.x + randomJitter(42);
          node.ty = center.y + randomJitter(32);
        });
        groups.forEach((group) => {
          const center = centers.get(group);
          if (!center) {
            return;
          }
          labels.push({ text: group, x: center.x, y: center.y - 52 });
        });
      }

      if (mode === "risk") {
        const groups = ["Auto Convertible", "Manual Review"];
        const centers = new Map([
          [groups[0], { x: state.width * 0.33, y: state.height * 0.54 }],
          [groups[1], { x: state.width * 0.72, y: state.height * 0.54 }],
        ]);

        nodes.forEach((node) => {
          const group = node.row.needs_manual_review ? groups[1] : groups[0];
          const center = centers.get(group);
          if (!center) {
            return;
          }
          node.group = group;
          node.tx = center.x + randomJitter(68);
          node.ty = center.y + randomJitter(78);
        });

        labels.push(
          { text: "Auto Convertible", x: state.width * 0.33, y: state.height * 0.22 },
          { text: "Manual Review", x: state.width * 0.72, y: state.height * 0.22 }
        );
      }

      if (mode === "workload") {
        const maxExecutions = Math.max(...rows.map((row) => row.executions));
        const minExecutions = Math.min(...rows.map((row) => row.executions));
        nodes.forEach((node) => {
          const xRatio =
            (Math.log10(node.row.executions + 1) - Math.log10(minExecutions + 1)) /
            (Math.log10(maxExecutions + 1) - Math.log10(minExecutions + 1) || 1);
          const yRatio = (Number(node.row.complexity) - 1) / 9;
          node.group = "workload";
          node.tx = 68 + xRatio * (state.width - 130) + randomJitter(8);
          node.ty = state.height - 58 - yRatio * (state.height - 116) + randomJitter(8);
        });

        labels.push(
          { text: "Low Frequency", x: 110, y: state.height - 18 },
          { text: "High Frequency", x: state.width - 120, y: state.height - 18 },
          { text: "High Complexity", x: 102, y: 22 }
        );
      }

      modeCaption.textContent = modeMeta[mode].caption;
      modeInsight.textContent = modeMeta[mode].insight;
      renderModeContext(mode, rows, topTables, stats);
      renderClusterLabels(labels);
      highlightModeButton(mode);
    }

    /**
     * @param {Array<{text: string, x: number, y: number}>} labels
     */
    function renderClusterLabels(labels) {
      labelsRoot.innerHTML = labels
        .map(
          (label) =>
            `<span class="cluster-label" style="left:${label.x}px;top:${label.y}px">${escapeHtml(label.text)}</span>`
        )
        .join("");
    }

    function tick() {
      ctx.fillStyle = "rgba(8, 17, 24, 0.17)";
      ctx.fillRect(0, 0, state.width, state.height);

      const highlight = findNearestNode(state.pointerX, state.pointerY, 15);
      state.hoverId = highlight?.index ?? -1;

      ctx.save();
      ctx.globalCompositeOperation = "screen";
      nodes.forEach((node) => {
        const forceX = (node.tx - node.x) * 0.028;
        const forceY = (node.ty - node.y) * 0.028;
        node.vx = (node.vx + forceX + randomJitter(0.02)) * 0.88;
        node.vy = (node.vy + forceY + randomJitter(0.02)) * 0.88;
        node.x += node.vx;
        node.y += node.vy;

        const baseColor = categoryColor[node.row.category] ?? "#d9d9d9";
        const alpha = state.hoverId === -1 || state.hoverId === node.index ? 0.88 : 0.34;
        drawNode(ctx, node.x, node.y, node.radius, baseColor, alpha, mode === "risk" && node.row.needs_manual_review);
      });
      ctx.restore();

      drawAxesIfNeeded();
      renderTooltip();
      window.requestAnimationFrame(tick);
    }

    function drawAxesIfNeeded() {
      if (mode !== "workload") {
        return;
      }
      ctx.save();
      ctx.strokeStyle = "rgba(214, 239, 251, 0.32)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(60, state.height - 54);
      ctx.lineTo(state.width - 40, state.height - 54);
      ctx.lineTo(state.width - 40, 40);
      ctx.stroke();
      ctx.restore();
    }

    function renderTooltip() {
      if (state.hoverId < 0) {
        tooltip.hidden = true;
        return;
      }

      const node = nodes[state.hoverId];
      if (!node) {
        tooltip.hidden = true;
        return;
      }

      const statusLabel = String(node.row.final_status).replace(/_/g, " ");
      tooltip.innerHTML = `
        <strong>${escapeHtml(node.row.script_file)}</strong>
        <div>${titleCase(node.row.category)} | Complexity ${node.row.complexity}/10</div>
        <div>${node.row.executions} executions | ${node.row.runtimeSec.toFixed(2)}s total runtime</div>
        <div>Final status: ${escapeHtml(statusLabel)}</div>
        <div><em>Click for source/target SQL + diff</em></div>
      `;

      const x = clamp(state.pointerX + 14, 8, state.width - 264);
      const y = clamp(state.pointerY + 14, 8, state.height - 150);
      tooltip.style.left = `${x}px`;
      tooltip.style.top = `${y}px`;
      tooltip.hidden = false;
    }

    function highlightModeButton(selectedMode) {
      $$(".mode-btn").forEach((button) => {
        button.classList.toggle("active", button.dataset.mode === selectedMode);
      });
    }

    function drawNode(ctx2d, x, y, radius, color, alpha, square = false) {
      ctx2d.fillStyle = hexToRgba(color, alpha);
      if (square) {
        const side = radius * 1.7;
        ctx2d.fillRect(x - side / 2, y - side / 2, side, side);
        return;
      }
      ctx2d.beginPath();
      ctx2d.arc(x, y, radius, 0, Math.PI * 2);
      ctx2d.fill();
    }

    function randomJitter(max) {
      return (Math.random() - 0.5) * max * 2;
    }

    /**
     * @param {number} x
     * @param {number} y
     * @param {number} threshold
     */
    function findNearestNode(x, y, threshold) {
      let nearest = null;
      let best = threshold * threshold;
      nodes.forEach((node) => {
        const dx = node.x - x;
        const dy = node.y - y;
        const dist = dx * dx + dy * dy;
        if (dist < best) {
          best = dist;
          nearest = node;
        }
      });
      return nearest;
    }

    canvas.addEventListener("mousemove", (event) => {
      const rect = canvas.getBoundingClientRect();
      state.pointerX = event.clientX - rect.left;
      state.pointerY = event.clientY - rect.top;
    });

    canvas.addEventListener("mouseleave", () => {
      state.pointerX = -1000;
      state.pointerY = -1000;
      state.hoverId = -1;
      tooltip.hidden = true;
    });

    canvas.addEventListener("click", (event) => {
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      const hit = findNearestNode(x, y, 18);
      if (hit) {
        onNodeOpen(hit.row);
      }
    });

    $$(".mode-btn").forEach((button) => {
      button.addEventListener("click", () => {
        const nextMode = button.dataset.mode;
        if (!nextMode) {
          return;
        }
        applyMode(nextMode);
      });
    });

    window.addEventListener("resize", resize, { passive: true });

    resize();
    applyMode(mode);
    tick();
  }

  /**
   * @param {ReturnType<typeof buildSummary>} stats
   */
  function setupSimulator(stats) {
    const volumeEl = /** @type {HTMLInputElement | null} */ ($("#sim-volume"));
    const loadEl = /** @type {HTMLInputElement | null} */ ($("#sim-load"));
    const qualityEl = /** @type {HTMLInputElement | null} */ ($("#sim-quality"));
    const verifyEl = /** @type {HTMLInputElement | null} */ ($("#sim-verify"));

    if (!volumeEl || !loadEl || !qualityEl || !verifyEl) {
      return;
    }

    const volumeValue = $("#sim-volume-value");
    const loadValue = $("#sim-load-value");
    const qualityValue = $("#sim-quality-value");
    const verifyValue = $("#sim-verify-value");

    const manualCostEl = $("#sim-manual-cost");
    const llmCostEl = $("#sim-llm-cost");
    const manualTimeEl = $("#sim-manual-time");
    const llmTimeEl = $("#sim-llm-time");
    const incidentReductionEl = $("#sim-incident-reduction");
    const defectRateEl = $("#sim-defect-rate");
    const valueEl = $("#sim-value");
    const roiEl = $("#sim-roi");

    const fmtCurrency = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    });

    function compute() {
      const volume = Number(volumeEl.value);
      const loadScale = Number(loadEl.value) / 100;
      const quality = Number(qualityEl.value) / 100;
      const verification = Number(verifyEl.value) / 100;

      if (volumeValue) volumeValue.textContent = String(volume);
      if (loadValue) loadValue.textContent = `${loadScale.toFixed(1)}x`;
      if (qualityValue) qualityValue.textContent = `${Math.round(quality * 100)}%`;
      if (verifyValue) verifyValue.textContent = `${Math.round(verification * 100)}%`;

      const teamSize = 5;
      const hoursPerWeekPerEngineer = 35;
      const hourlyRate = 145;

      const manualHoursPerScript = 7.8 + 0.65 * stats.avgComplexity + 0.45 * loadScale;
      const manualHours = volume * manualHoursPerScript;
      const manualWeeks = manualHours / (teamSize * hoursPerWeekPerEngineer);
      const manualCost = manualHours * hourlyRate;

      const autoPassRate = clamp((stats.firstPassRate / 100) * quality + 0.22 * verification - 0.08, 0.35, 0.98);
      const reviewShare = clamp((stats.manualReviewRate / 100) + (1 - quality) * 0.52 - verification * 0.17, 0.08, 0.75);
      const attemptsPerScript = 1 + (1 - autoPassRate) * 1.9;
      const llmHoursPerScript = 1.4 + reviewShare * 5.6 + (1 - quality) * 2.8 + (1 - verification) * 1.6;
      const llmHours = volume * llmHoursPerScript;
      const llmWeeks = llmHours / (teamSize * hoursPerWeekPerEngineer);
      const llmCost = llmHours * hourlyRate + volume * attemptsPerScript * 1.1;

      const manualDefectRate = clamp(0.1 - verification * 0.025 + (1 - quality) * 0.03, 0.03, 0.16);
      const llmDefectRate = clamp(0.06 * (1 - quality) + 0.05 * (1 - verification), 0.007, 0.11);
      const incidentFactor = 0.32 + loadScale * 0.14;
      const manualIncidents = volume * manualDefectRate * incidentFactor;
      const llmIncidents = volume * llmDefectRate * incidentFactor;
      const incidentReduction = manualIncidents - llmIncidents;

      const monthlyRuntimeSec = stats.runtimePerScriptSec * volume * loadScale;
      const runtimeGain = clamp(0.08 + quality * 0.16 + verification * 0.14, 0.12, 0.46);
      const runtimeSavedHours = (monthlyRuntimeSec * runtimeGain) / 3600;
      const valueFromPerf = runtimeSavedHours * 420;
      const valueFromRisk = incidentReduction * 3200;
      const valueFromDelivery = Math.max(0, manualWeeks - llmWeeks) * 18000;
      const businessValue = valueFromPerf + valueFromRisk + valueFromDelivery;
      const roi = llmCost > 0 ? businessValue / llmCost : 0;

      if (manualCostEl) manualCostEl.textContent = fmtCurrency.format(manualCost);
      if (llmCostEl) llmCostEl.textContent = fmtCurrency.format(llmCost);
      if (manualTimeEl) manualTimeEl.textContent = `${manualWeeks.toFixed(1)} weeks for a 5-engineer team`;
      if (llmTimeEl) llmTimeEl.textContent = `${llmWeeks.toFixed(1)} weeks, avg ${attemptsPerScript.toFixed(2)} attempts/script`;
      if (incidentReductionEl)
        incidentReductionEl.textContent = `${incidentReduction.toFixed(1)} fewer incident-equivalents / month`;
      if (defectRateEl)
        defectRateEl.textContent = `Defect risk ${Math.round(llmDefectRate * 1000) / 10}% (manual ${Math.round(
          manualDefectRate * 1000
        ) / 10}%)`;
      if (valueEl) valueEl.textContent = fmtCurrency.format(businessValue);
      if (roiEl) roiEl.textContent = `ROI ${roi.toFixed(2)}x (modeled)`;
    }

    [volumeEl, loadEl, qualityEl, verifyEl].forEach((input) => {
      input.addEventListener("input", compute);
      input.addEventListener("change", compute);
    });

    compute();
  }

  /**
   * @param {ReturnType<typeof buildSummary>} stats
   */
  function setupProcessCards(stats) {
    const steps = [
      {
        title: "Fingerprint Workload",
        kicker: "Classify before translating.",
        cardText: "Build an execution and risk fingerprint from logs + script metadata.",
        description:
          "We parse execution logs, complexity, tags, and table touch patterns to route scripts by migration risk. This avoids wasting review effort on trivial conversions.",
        proof: `${stats.scriptCount} scripts analyzed, ${stats.totalExecutions.toLocaleString()} executions observed.`,
        svg: svgStepFingerprint(),
      },
      {
        title: "Route by Strategy",
        kicker: "Different scripts need different playbooks.",
        cardText: "Auto-route safe patterns, escalate structural rewrites.",
        description:
          "Scripts are routed into strategy lanes: direct syntax rewrite, structural rewrite (MERGE/PIVOT/CROSS APPLY), and manual-supervised conversion for transaction-heavy or dynamic SQL patterns.",
        proof: `${stats.manualReviewRate.toFixed(0)}% routed to high-touch lanes; rest stays in fast path.`,
        svg: svgStepRouting(),
      },
      {
        title: "Generate Draft SQL",
        kicker: "Rules + LLM, not LLM alone.",
        cardText: "Use rule constraints to keep generation grounded.",
        description:
          "Prompt templates inject mapping rules for data types, date functions, and dialect-specific constructs. The model drafts MySQL SQL with explicit transformation notes.",
        proof: `First-pass conversion succeeds for ${stats.firstPassRate.toFixed(0)}% of scripts in this dataset.`,
        svg: svgStepDraft(),
      },
      {
        title: "Verify Equivalence",
        kicker: "Syntax pass is not enough.",
        cardText: "Run schema checks, invariant tests, and synthetic edge cases.",
        description:
          "Each conversion runs automated checks: parse/lint, schema compatibility, row-count parity, and business invariants on synthetic and sampled payloads.",
        proof: "Verification catches silent drift in null semantics, rounding, and transaction behavior.",
        svg: svgStepVerify(),
      },
      {
        title: "Auto-Correct Loop",
        kicker: "Failed checks feed targeted prompts.",
        cardText: "Regenerate only the risky region and re-test.",
        description:
          "Failures are fed back with scoped diffs and failing assertions. The model revises only vulnerable fragments, reducing churn and preserving known-good logic.",
        proof: `Average attempts/script: ${stats.avgAttempts.toFixed(2)}.`,
        svg: svgStepFix(),
      },
      {
        title: "Ship with Guardrails",
        kicker: "Production rollout must stay observable.",
        cardText: "Deliver SQL + evidence + rollback hooks.",
        description:
          "Deployment bundles converted scripts, verification artifacts, and canary metrics. Monitoring compares latency, row deltas, and error signatures before full cutover.",
        proof: `Final pass rate after iteration: ${stats.finalPassRate.toFixed(0)}% in this synthetic workload.`,
        svg: svgStepDeploy(),
      },
    ];

    const cardsRoot = $("#process-cards");
    const stepTitle = $("#step-title");
    const stepKicker = $("#step-kicker");
    const stepDescription = $("#step-description");
    const stepProof = $("#step-proof");
    const stepSvg = $("#step-svg");

    if (!cardsRoot || !stepTitle || !stepKicker || !stepDescription || !stepProof || !stepSvg) {
      return;
    }

    cardsRoot.innerHTML = steps
      .map(
        (step, index) => `
        <button type="button" class="process-card ${index === 0 ? "active" : ""}" data-step-index="${index}" role="tab" aria-selected="${
          index === 0 ? "true" : "false"
        }">
          <span class="step-index">Step ${index + 1}</span>
          <h3>${escapeHtml(step.title)}</h3>
          <p>${escapeHtml(step.cardText)}</p>
        </button>
      `
      )
      .join("");

    const activate = (index) => {
      const step = steps[index];
      if (!step) {
        return;
      }

      stepTitle.textContent = step.title;
      stepKicker.textContent = step.kicker;
      stepDescription.textContent = step.description;
      stepProof.textContent = step.proof;
      stepSvg.innerHTML = step.svg;

      $$(".process-card", cardsRoot).forEach((card, cardIndex) => {
        const active = cardIndex === index;
        card.classList.toggle("active", active);
        card.setAttribute("aria-selected", active ? "true" : "false");
      });
    };

    cardsRoot.addEventListener("click", (event) => {
      const button = /** @type {HTMLElement | null} */ (
        event.target instanceof HTMLElement ? event.target.closest(".process-card") : null
      );
      if (!button) {
        return;
      }
      const stepIndex = Number(button.dataset.stepIndex);
      activate(stepIndex);
    });

    activate(0);
  }

  /**
   * @param {Array<any>} rows
   * @param {{byFile?: Record<string, {script_id:number, mssql:string, mysql:string}>} | undefined} sqlStore
   */
  function setupExamplePanel(rows, sqlStore) {
    const byId = new Map(rows.map((row) => [Number(row.script_id), row]));

    const examples = [
      {
        key: "openjson",
        label: "0080 OPENJSON ETL",
        scriptId: 80,
        why:
          "High runtime ETL script. The non-obvious challenge is preserving numeric precision and JSON path typing when moving from OPENJSON to JSON_TABLE.",
        mssql: [
          "DECLARE @orderId BIGINT = 12345;",
          "DECLARE @items NVARCHAR(MAX) = N'['",
          "  {\"ProductID\": 10, \"Quantity\": 2, \"UnitPrice\": 19.99, \"Discount\": 0}",
          "]';",
          "",
          "INSERT INTO [dbo].[OrderItems]([OrderID],[ProductID],[Quantity],[UnitPrice],[Discount],[LineTotal])",
          "SELECT @orderId, j.[ProductID], j.[Quantity], j.[UnitPrice], j.[Discount],",
          "       (j.[Quantity] * j.[UnitPrice]) - j.[Discount] AS [LineTotal]",
          "FROM OPENJSON(@items)",
          "WITH (",
          "  [ProductID] INT '$.ProductID',",
          "  [Quantity] INT '$.Quantity',",
          "  [UnitPrice] MONEY '$.UnitPrice',",
          "  [Discount] MONEY '$.Discount'",
          ") j;",
        ].join("\n"),
        mysql: [
          "SET @orderId := 12345;",
          "SET @items := JSON_ARRAY(JSON_OBJECT('ProductID', 10, 'Quantity', 2, 'UnitPrice', 19.99, 'Discount', 0));",
          "",
          "INSERT INTO OrderItems (OrderID, ProductID, Quantity, UnitPrice, Discount, LineTotal)",
          "SELECT @orderId, jt.ProductID, jt.Quantity, jt.UnitPrice, jt.Discount,",
          "       (jt.Quantity * jt.UnitPrice) - jt.Discount AS LineTotal",
          "FROM JSON_TABLE(@items, '$[*]'",
          "  COLUMNS (",
          "    ProductID INT PATH '$.ProductID',",
          "    Quantity INT PATH '$.Quantity',",
          "    UnitPrice DECIMAL(19,4) PATH '$.UnitPrice',",
          "    Discount DECIMAL(19,4) PATH '$.Discount'",
          "  )",
          ") AS jt;",
        ].join("\n"),
        mappings: [
          {
            from: "OPENJSON ... WITH (...)",
            to: "JSON_TABLE(... COLUMNS ... PATH)",
            sourcePatterns: ["OPENJSON(@items)", "WITH (", "UnitPrice MONEY", "Discount MONEY"],
            targetPatterns: ["JSON_TABLE(@items", "COLUMNS (", "UnitPrice DECIMAL(19,4)", "Discount DECIMAL(19,4)"],
            insight:
              "Both parse JSON, but MySQL column typing must be explicit up front. Missing precision here cascades into accounting drift later.",
          },
          {
            from: "MONEY",
            to: "DECIMAL(19,4)",
            sourcePatterns: ["UnitPrice MONEY", "Discount MONEY"],
            targetPatterns: ["UnitPrice DECIMAL(19,4)", "Discount DECIMAL(19,4)"],
            insight:
              "The conversion is not stylistic; it controls rounding and reconciliation behavior in financial line totals.",
          },
          {
            from: "NVARCHAR(MAX) payload literal",
            to: "JSON_ARRAY / JSON_OBJECT",
            sourcePatterns: ["DECLARE @items NVARCHAR(MAX)", "{\"ProductID\""],
            targetPatterns: ["SET @items := JSON_ARRAY", "JSON_OBJECT('ProductID'"],
            insight:
              "Structured JSON constructors reduce malformed payload risk and simplify synthetic test generation.",
          },
        ],
        timeline: [
          "Classified as ETL + JSON high risk because OPENJSON and MONEY appear together.",
          "Routing engine marked it for structural rewrite and precision checks.",
          "First model draft passed syntax but flagged manual review for JSON typing.",
          "Generated synthetic payloads with missing and decimal-heavy fields; row and total invariants failed once.",
          "Repair prompt constrained type map to DECIMAL(19,4) and added explicit PATH columns.",
          "Canary rollout compared OrderItems totals for five days before full switch.",
        ],
      },
      {
        key: "merge",
        label: "0076 MERGE UPSERT",
        scriptId: 76,
        why:
          "Core inventory ETL script. The non-obvious challenge is that MySQL has no direct MERGE equivalent; correctness depends on key design.",
        mssql: [
          "MERGE [dbo].[InventoryMovements] AS tgt",
          "USING (",
          "  SELECT [ProductID],[StoreID],[MovementType],[Quantity],[MovedAt],[Reference]",
          "  FROM [dbo].[StgInventoryMovements]",
          ") AS src",
          "ON tgt.[ProductID] = src.[ProductID]",
          " AND tgt.[StoreID] = src.[StoreID]",
          " AND tgt.[MovedAt] = src.[MovedAt]",
          " AND ISNULL(tgt.[Reference],'') = ISNULL(src.[Reference],'')",
          "WHEN MATCHED THEN",
          "  UPDATE SET tgt.[Quantity] = src.[Quantity]",
          "WHEN NOT MATCHED THEN",
          "  INSERT ([ProductID],[StoreID],[MovementType],[Quantity],[MovedAt],[Reference])",
          "  VALUES (src.[ProductID],src.[StoreID],src.[MovementType],src.[Quantity],src.[MovedAt],src.[Reference]);",
        ].join("\n"),
        mysql: [
          "-- prerequisite: UNIQUE KEY(ProductID, StoreID, MovedAt, Reference)",
          "INSERT INTO InventoryMovements (ProductID, StoreID, MovementType, Quantity, MovedAt, Reference)",
          "SELECT s.ProductID, s.StoreID, s.MovementType, s.Quantity, s.MovedAt, s.Reference",
          "FROM StgInventoryMovements s",
          "ON DUPLICATE KEY UPDATE",
          "  Quantity = VALUES(Quantity),",
          "  MovementType = VALUES(MovementType);",
        ].join("\n"),
        mappings: [
          {
            from: "MERGE ... WHEN MATCHED / NOT MATCHED",
            to: "INSERT ... ON DUPLICATE KEY UPDATE",
            sourcePatterns: ["MERGE [dbo].[InventoryMovements]", "WHEN MATCHED", "WHEN NOT MATCHED"],
            targetPatterns: ["INSERT INTO InventoryMovements", "ON DUPLICATE KEY UPDATE"],
            insight:
              "The SQL rewrite only works if a natural key is explicitly enforced. Without that unique key, duplicates silently accumulate.",
          },
          {
            from: "ISNULL(tgt.Reference,'') = ISNULL(src.Reference,'')",
            to: "Key-normalization decision during key design",
            sourcePatterns: ["ISNULL(tgt.[Reference],''", "ISNULL(src.[Reference],''", "ISNULL(tgt.[Reference],'') = ISNULL(src.[Reference],'')"],
            targetPatterns: ["UNIQUE KEY(ProductID, StoreID, MovedAt, Reference)"],
            insight:
              "Null-equality logic must move from query text into key and data-cleanup policy, or behavior diverges.",
          },
          {
            from: "Single MERGE statement semantics",
            to: "Insert path + update path under key collision",
            sourcePatterns: ["MERGE", "WHEN MATCHED", "WHEN NOT MATCHED"],
            targetPatterns: ["ON DUPLICATE KEY UPDATE", "VALUES(Quantity)", "VALUES(MovementType)"],
            insight:
              "Locking and race behavior changes. Verification must include concurrent upsert tests, not just functional snapshots.",
          },
        ],
        timeline: [
          "Fingerprinting tagged MERGE + upsert + high runtime concentration.",
          "Routing logic selected structural rewrite and concurrency validation lane.",
          "Attempt 1 translated syntax but failed governance check: no natural key specified.",
          "Generated synthetic staging rows with duplicate movement keys and null references.",
          "Attempt 2 added ON DUPLICATE KEY pattern with explicit key prerequisite and passed parity checks.",
          "Rollout guardrail tracked duplicate-rate and inventory deltas before enabling full ETL schedule.",
        ],
      },
      {
        key: "pivot",
        label: "0010 PIVOT REPORT",
        scriptId: 10,
        why:
          "Reporting script with structural transformation. The key point is moving from a SQL Server PIVOT operator to explicit conditional aggregation in MySQL.",
        mssql: [
          "DECLARE @year INT = YEAR(GETDATE());",
          "",
          "SELECT *",
          "FROM (",
          "  SELECT s.[StoreName], MONTH(o.[OrderDate]) AS [OrderMonth], SUM(o.[Total]) AS [Revenue]",
          "  FROM [dbo].[Orders] o",
          "  JOIN [dbo].[Stores] s ON s.[StoreID] = o.[StoreID]",
          "  WHERE YEAR(o.[OrderDate]) = @year",
          "  GROUP BY s.[StoreName], MONTH(o.[OrderDate])",
          ") src",
          "PIVOT (",
          "  SUM([Revenue]) FOR [OrderMonth] IN ([1],[2],[3],[4],[5],[6],[7],[8],[9],[10],[11],[12])",
          ") p",
          "ORDER BY [StoreName];",
        ].join("\n"),
        mysql: [
          "SET @year := YEAR(NOW());",
          "",
          "SELECT",
          "  s.`StoreName`,",
          "  SUM(CASE WHEN MONTH(o.`OrderDate`) = 1 THEN o.`Total` ELSE 0 END) AS `M01`,",
          "  SUM(CASE WHEN MONTH(o.`OrderDate`) = 2 THEN o.`Total` ELSE 0 END) AS `M02`,",
          "  ...",
          "  SUM(CASE WHEN MONTH(o.`OrderDate`) = 12 THEN o.`Total` ELSE 0 END) AS `M12`",
          "FROM `Orders` o",
          "JOIN `Stores` s ON s.`StoreID` = o.`StoreID`",
          "WHERE YEAR(o.`OrderDate`) = @year",
          "GROUP BY s.`StoreName`",
          "ORDER BY s.`StoreName`;",
        ].join("\n"),
        mappings: [
          {
            from: "PIVOT (...)",
            to: "SUM(CASE WHEN ... THEN ... END)",
            sourcePatterns: ["PIVOT (", "FOR [OrderMonth] IN"],
            targetPatterns: ["SUM(CASE WHEN MONTH(o.`OrderDate`)", "AS `M01`", "AS `M12`"],
            insight:
              "This rewrite expands one operator into 12 explicit expressions. It is easier to tune but can hide mistakes in month indexing.",
          },
          {
            from: "SELECT * from pivoted source",
            to: "Explicit month columns",
            sourcePatterns: ["SELECT *", ") src"],
            targetPatterns: ["SELECT", "AS `M01`", "AS `M12`"],
            insight:
              "Explicit projection makes downstream schema contracts clearer and avoids accidental column order drift.",
          },
          {
            from: "YEAR(GETDATE())",
            to: "YEAR(NOW())",
            sourcePatterns: ["YEAR(GETDATE())", "@year"],
            targetPatterns: ["YEAR(NOW())", "@year"],
            insight:
              "Date-function swaps are simple syntactically, but time zone and session settings still require validation in production.",
          },
        ],
        timeline: [
          "Classifier marked this as structural rewrite due to PIVOT tag and complexity 8/10.",
          "Router selected reporting lane with performance-sensitive verification.",
          "Draft conversion expanded PIVOT into month-by-month CASE aggregations.",
          "Synthetic checks validated month completeness and yearly totals per store.",
          "Optimizer review recommended covering index on (StoreID, OrderDate, OrderStatus).",
          "Rollout compared report totals against SQL Server baseline for two close cycles.",
        ],
      },
    ];

    const tabsRoot = $("#example-tabs");
    const contentRoot = $("#example-content");
    if (!tabsRoot || !contentRoot) {
      return;
    }

    tabsRoot.innerHTML = examples
      .map(
        (example, index) =>
          `<button type="button" class="example-tab ${index === 0 ? "active" : ""}" data-example="${example.key}" role="tab">${escapeHtml(
            example.label
          )}</button>`
      )
      .join("");

    function render(exampleKey) {
      const selected = examples.find((item) => item.key === exampleKey) ?? examples[0];
      const script = byId.get(selected.scriptId);
      if (!script) {
        return;
      }

      const fallbackSql = sqlStore?.byFile?.[script.script_file];
      const sourceSql = selected.mssql ?? fallbackSql?.mssql ?? "-- source unavailable";
      const targetSql = selected.mysql ?? fallbackSql?.mysql ?? "-- target unavailable";
      const statusClass = script.final_status === "failed" ? "warn" : "ok";

      contentRoot.innerHTML = `
        <article class="example-shell">
          <p>${escapeHtml(selected.why)}</p>
          <div class="example-head">
            <article>
              <h4>Observed Runtime</h4>
              <p>${script.runtimeSec.toFixed(2)} s total</p>
            </article>
            <article>
              <h4>Execution Count</h4>
              <p>${Number(script.executions).toLocaleString()} runs</p>
            </article>
            <article>
              <h4>Conversion Attempts</h4>
              <p>${script.conversion_attempts} attempts</p>
            </article>
            <article>
              <h4>Final Status</h4>
              <p class="${statusClass}">${escapeHtml(String(script.final_status).replace(/_/g, " "))}</p>
            </article>
          </div>

          <div class="code-compare">
            <section class="code-panel">
              <h4>MSSQL Source</h4>
              ${renderSqlBlockFromText(sourceSql, "example-source-block")}
            </section>
            <section class="code-panel">
              <h4>MySQL Target</h4>
              ${renderSqlBlockFromText(targetSql, "example-target-block")}
            </section>
          </div>

          <div class="mapping-grid">
            ${selected.mappings
              .map(
                (item) => `
              <article
                class="mapping-item"
                tabindex="0"
                data-source-patterns="${escapeHtml(item.sourcePatterns.join("||"))}"
                data-target-patterns="${escapeHtml(item.targetPatterns.join("||"))}"
              >
                <h5>Mapping</h5>
                <code>${escapeHtml(item.from)}</code>
                <code>${escapeHtml(item.to)}</code>
                <p>${escapeHtml(item.insight)}</p>
              </article>`
              )
              .join("")}
          </div>

          <section class="timeline">
            <h4>How the six-step process played out (synthetic but realistic)</h4>
            <div class="timeline-grid">
              ${selected.timeline
                .map(
                  (step, index) => `
                <article class="timeline-step">
                  <strong>Step ${index + 1}</strong>
                  <p>${escapeHtml(step)}</p>
                </article>`
                )
                .join("")}
            </div>
          </section>
        </article>
      `;

      wireMappingHighlights(contentRoot);
    }

    tabsRoot.addEventListener("click", (event) => {
      const button = /** @type {HTMLElement | null} */ (
        event.target instanceof HTMLElement ? event.target.closest(".example-tab") : null
      );
      if (!button) {
        return;
      }
      const key = button.dataset.example;
      if (!key) {
        return;
      }

      $$(".example-tab", tabsRoot).forEach((tab) => tab.classList.toggle("active", tab === button));
      render(key);
    });

    render(examples[0].key);
  }

  /**
   * @param {HTMLElement} root
   */
  function wireMappingHighlights(root) {
    const sourceBlock = $(".example-source-block", root);
    const targetBlock = $(".example-target-block", root);
    if (!sourceBlock || !targetBlock) {
      return;
    }

    const clearHighlights = () => {
      $$(".sql-line.line-emphasis", root).forEach((line) => line.classList.remove("line-emphasis"));
    };

    $$(".mapping-item", root).forEach((item) => {
      const activate = () => {
        clearHighlights();
        highlightSqlLines(sourceBlock, parsePatternAttr(item.dataset.sourcePatterns));
        highlightSqlLines(targetBlock, parsePatternAttr(item.dataset.targetPatterns));
      };

      item.addEventListener("mouseenter", activate);
      item.addEventListener("focus", activate);
      item.addEventListener("mouseleave", clearHighlights);
      item.addEventListener("blur", clearHighlights);
    });
  }

  function svgStepFingerprint() {
    return `
      <svg viewBox="0 0 560 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Workload fingerprint animation">
        <defs>
          <linearGradient id="gradA" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#67dbf3" />
            <stop offset="100%" stop-color="#f7bd5e" />
          </linearGradient>
        </defs>
        <rect x="16" y="20" width="528" height="200" rx="18" fill="rgba(12,28,36,0.65)" stroke="rgba(110,196,225,0.45)" />
        <g class="svg-drift">
          <circle cx="76" cy="82" r="7" fill="#67dbf3" class="svg-pulse" />
          <circle cx="94" cy="122" r="6" fill="#ffd17e" class="svg-pulse" />
          <circle cx="72" cy="160" r="5" fill="#8ce3a8" class="svg-pulse" />
          <circle cx="130" cy="95" r="5" fill="#ffd17e" class="svg-pulse" />
          <circle cx="138" cy="146" r="7" fill="#67dbf3" class="svg-pulse" />
        </g>
        <line x1="160" y1="120" x2="278" y2="120" stroke="url(#gradA)" stroke-width="3" class="svg-flow-line" />
        <rect x="284" y="58" width="236" height="126" rx="12" fill="rgba(28,66,82,0.78)" stroke="rgba(130,216,240,0.5)" />
        <rect x="302" y="75" width="36" height="24" rx="4" fill="#ff9b67" class="svg-blink" />
        <rect x="348" y="75" width="36" height="24" rx="4" fill="#7be2f6" class="svg-blink" />
        <rect x="394" y="75" width="36" height="24" rx="4" fill="#91f3b4" class="svg-blink" />
        <rect x="440" y="75" width="36" height="24" rx="4" fill="#c4b0ff" class="svg-blink" />
        <rect x="302" y="107" width="36" height="24" rx="4" fill="#7be2f6" class="svg-blink" />
        <rect x="348" y="107" width="36" height="24" rx="4" fill="#ff9b67" class="svg-blink" />
        <rect x="394" y="107" width="36" height="24" rx="4" fill="#ffd17e" class="svg-blink" />
        <rect x="440" y="107" width="36" height="24" rx="4" fill="#8ce3a8" class="svg-blink" />
        <rect x="302" y="139" width="36" height="24" rx="4" fill="#8ce3a8" class="svg-blink" />
        <rect x="348" y="139" width="36" height="24" rx="4" fill="#ffd17e" class="svg-blink" />
        <rect x="394" y="139" width="36" height="24" rx="4" fill="#67dbf3" class="svg-blink" />
        <rect x="440" y="139" width="36" height="24" rx="4" fill="#ff9b67" class="svg-blink" />
      </svg>
    `;
  }

  function svgStepRouting() {
    return `
      <svg viewBox="0 0 560 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Strategy routing animation">
        <rect x="20" y="26" width="520" height="188" rx="16" fill="rgba(10,28,36,0.66)" stroke="rgba(112,196,220,0.45)" />
        <rect x="44" y="86" width="94" height="68" rx="9" fill="rgba(114,220,242,0.15)" stroke="#74dff3" />
        <text x="91" y="123" fill="#d9f7ff" font-size="13" text-anchor="middle" font-family="IBM Plex Sans">Scripts</text>
        <line x1="140" y1="120" x2="212" y2="72" stroke="#f8c05f" stroke-width="3" class="svg-flow-line" />
        <line x1="140" y1="120" x2="212" y2="120" stroke="#73def2" stroke-width="3" class="svg-flow-line" />
        <line x1="140" y1="120" x2="212" y2="168" stroke="#9bf0ba" stroke-width="3" class="svg-flow-line" />

        <rect x="222" y="44" width="122" height="50" rx="8" fill="rgba(246,195,95,0.2)" stroke="#f8c05f" />
        <text x="283" y="73" fill="#f9e9bf" font-size="12" text-anchor="middle" font-family="IBM Plex Sans">Direct Rewrite</text>

        <rect x="222" y="94" width="122" height="50" rx="8" fill="rgba(115,222,242,0.19)" stroke="#73def2" />
        <text x="283" y="123" fill="#d5f8ff" font-size="12" text-anchor="middle" font-family="IBM Plex Sans">Structural Rewrite</text>

        <rect x="222" y="144" width="122" height="50" rx="8" fill="rgba(155,240,186,0.19)" stroke="#9bf0ba" />
        <text x="283" y="173" fill="#defbe9" font-size="12" text-anchor="middle" font-family="IBM Plex Sans">Manual Supervision</text>

        <rect x="380" y="58" width="132" height="124" rx="10" fill="rgba(38,70,83,0.72)" stroke="#8dd9ef" />
        <text x="446" y="84" fill="#ebfbff" font-size="12" text-anchor="middle" font-family="IBM Plex Sans">Risk Router</text>
        <circle cx="408" cy="108" r="7" fill="#73def2" class="svg-pulse" />
        <circle cx="446" cy="108" r="7" fill="#f8c05f" class="svg-pulse" />
        <circle cx="484" cy="108" r="7" fill="#9bf0ba" class="svg-pulse" />
        <line x1="408" y1="129" x2="484" y2="129" stroke="#7ed8f1" stroke-width="2" />
        <line x1="446" y1="129" x2="446" y2="158" stroke="#f2cd8f" stroke-width="2" class="svg-flow-line" />
      </svg>
    `;
  }

  function svgStepDraft() {
    return `
      <svg viewBox="0 0 560 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Draft generation animation">
        <rect x="16" y="20" width="528" height="200" rx="18" fill="rgba(12,28,36,0.66)" stroke="rgba(115,202,229,0.45)" />
        <rect x="42" y="48" width="200" height="144" rx="10" fill="rgba(42,75,90,0.78)" stroke="#76def3" />
        <text x="60" y="76" fill="#dff8ff" font-size="12" font-family="JetBrains Mono">SELECT TOP (100) ...</text>
        <text x="60" y="98" fill="#dff8ff" font-size="12" font-family="JetBrains Mono">MERGE ... WHEN MATCHED</text>
        <text x="60" y="120" fill="#dff8ff" font-size="12" font-family="JetBrains Mono">OPENJSON(@payload)</text>

        <polygon points="266,120 302,96 302,144" fill="#f7c05e" class="svg-pulse" />

        <rect x="318" y="48" width="200" height="144" rx="10" fill="rgba(29,72,81,0.82)" stroke="#9ceebe" />
        <text x="336" y="76" fill="#e6fff5" font-size="12" font-family="JetBrains Mono">SELECT ... LIMIT 100</text>
        <text x="336" y="98" fill="#e6fff5" font-size="12" font-family="JetBrains Mono">INSERT ... ON DUPLICATE</text>
        <text x="336" y="120" fill="#e6fff5" font-size="12" font-family="JetBrains Mono">JSON_TABLE(@payload)</text>

        <line x1="258" y1="74" x2="306" y2="74" stroke="#77dff3" stroke-width="2" class="svg-flow-line" />
        <line x1="258" y1="98" x2="306" y2="98" stroke="#77dff3" stroke-width="2" class="svg-flow-line" />
        <line x1="258" y1="122" x2="306" y2="122" stroke="#77dff3" stroke-width="2" class="svg-flow-line" />
      </svg>
    `;
  }

  function svgStepVerify() {
    return `
      <svg viewBox="0 0 560 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Verification animation">
        <rect x="18" y="24" width="524" height="192" rx="16" fill="rgba(11,28,36,0.67)" stroke="rgba(115,200,228,0.45)" />
        <rect x="44" y="56" width="180" height="120" rx="10" fill="rgba(41,73,89,0.8)" stroke="#78dff2" />
        <text x="134" y="84" fill="#def8ff" font-size="12" text-anchor="middle" font-family="IBM Plex Sans">Source Result</text>
        <rect x="56" y="96" width="156" height="14" rx="4" fill="#5fbad4" class="svg-blink" />
        <rect x="56" y="117" width="129" height="14" rx="4" fill="#8fe6b0" class="svg-blink" />
        <rect x="56" y="138" width="146" height="14" rx="4" fill="#f3c466" class="svg-blink" />

        <rect x="336" y="56" width="180" height="120" rx="10" fill="rgba(31,74,84,0.8)" stroke="#95efba" />
        <text x="426" y="84" fill="#e6fff2" font-size="12" text-anchor="middle" font-family="IBM Plex Sans">Target Result</text>
        <rect x="348" y="96" width="156" height="14" rx="4" fill="#5fbad4" class="svg-blink" />
        <rect x="348" y="117" width="129" height="14" rx="4" fill="#8fe6b0" class="svg-blink" />
        <rect x="348" y="138" width="146" height="14" rx="4" fill="#f3c466" class="svg-blink" />

        <line x1="224" y1="116" x2="336" y2="116" stroke="#f8c05f" stroke-width="3" class="svg-flow-line" />
        <circle cx="280" cy="116" r="15" fill="rgba(20,56,70,0.9)" stroke="#9beebc" class="svg-pulse" />
        <path d="M273 116l5 5 10-11" fill="none" stroke="#9beebc" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    `;
  }

  function svgStepFix() {
    return `
      <svg viewBox="0 0 560 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Auto-correction loop animation">
        <rect x="16" y="20" width="528" height="200" rx="18" fill="rgba(12,28,36,0.66)" stroke="rgba(115,202,229,0.45)" />
        <rect x="76" y="80" width="138" height="78" rx="10" fill="rgba(44,75,89,0.82)" stroke="#74def2" />
        <text x="145" y="112" fill="#dff9ff" font-size="12" text-anchor="middle" font-family="IBM Plex Sans">Draft SQL</text>

        <rect x="346" y="80" width="138" height="78" rx="10" fill="rgba(33,72,80,0.84)" stroke="#95efba" />
        <text x="415" y="112" fill="#eafff1" font-size="12" text-anchor="middle" font-family="IBM Plex Sans">Revised SQL</text>

        <circle cx="280" cy="118" r="24" fill="rgba(245,192,94,0.15)" stroke="#f7c05e" class="svg-pulse" />
        <path d="M280 94c13 0 24 11 24 24" fill="none" stroke="#f7c05e" stroke-width="2.4" />
        <path d="M304 118l-6-2 3-6" fill="#f7c05e" />
        <path d="M280 142c-13 0-24-11-24-24" fill="none" stroke="#95efba" stroke-width="2.4" />
        <path d="M256 118l6 2-3 6" fill="#95efba" />

        <line x1="214" y1="118" x2="256" y2="118" stroke="#74def2" stroke-width="3" class="svg-flow-line" />
        <line x1="304" y1="118" x2="346" y2="118" stroke="#95efba" stroke-width="3" class="svg-flow-line" />
      </svg>
    `;
  }

  function svgStepDeploy() {
    return `
      <svg viewBox="0 0 560 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Deployment guardrail animation">
        <rect x="16" y="20" width="528" height="200" rx="18" fill="rgba(12,28,36,0.66)" stroke="rgba(115,202,229,0.45)" />
        <rect x="56" y="58" width="150" height="124" rx="12" fill="rgba(33,72,80,0.8)" stroke="#74def2" />
        <text x="131" y="86" fill="#dff9ff" font-size="12" text-anchor="middle" font-family="IBM Plex Sans">Canary</text>
        <circle cx="131" cy="120" r="26" fill="rgba(116,222,242,0.15)" stroke="#74def2" class="svg-pulse" />
        <text x="131" y="124" fill="#dcf8ff" font-size="12" text-anchor="middle" font-family="JetBrains Mono">25%</text>

        <line x1="206" y1="120" x2="334" y2="120" stroke="#f7c05e" stroke-width="3" class="svg-flow-line" />

        <rect x="334" y="44" width="170" height="150" rx="12" fill="rgba(30,73,83,0.82)" stroke="#95efba" />
        <text x="419" y="72" fill="#ebfff4" font-size="12" text-anchor="middle" font-family="IBM Plex Sans">Production Guardrails</text>
        <line x1="356" y1="96" x2="482" y2="96" stroke="#8fe8b4" stroke-width="2" />
        <line x1="356" y1="122" x2="482" y2="122" stroke="#8fe8b4" stroke-width="2" />
        <line x1="356" y1="148" x2="482" y2="148" stroke="#8fe8b4" stroke-width="2" />
        <circle cx="362" cy="96" r="5" fill="#8fe8b4" class="svg-blink" />
        <circle cx="390" cy="122" r="5" fill="#f7c05e" class="svg-blink" />
        <circle cx="420" cy="148" r="5" fill="#74def2" class="svg-blink" />
      </svg>
    `;
  }

  /**
   * @param {string} sql
   * @param {string} blockClass
   */
  function renderSqlBlockFromText(sql, blockClass = "") {
    const lines = splitSqlLines(sql).map((text, index) => ({
      text,
      lineNo: index + 1,
      type: "same",
    }));
    return renderSqlBlockFromPrepared(lines, blockClass);
  }

  /**
   * @param {Array<{text: string, lineNo: number | null, type: "same"|"add"|"remove"|"empty"}>} lines
   * @param {string} blockClass
   */
  function renderSqlBlockFromPrepared(lines, blockClass = "") {
    return `
      <div class="sql-block ${blockClass}">
        ${lines.map((line) => renderSqlLine(line)).join("")}
      </div>
    `;
  }

  /**
   * @param {{text: string, lineNo: number | null, type: "same"|"add"|"remove"|"empty"}} line
   */
  function renderSqlLine(line) {
    const typeClass = line.type === "same" ? "" : `diff-${line.type}`;
    const lineNo = line.lineNo == null ? "" : String(line.lineNo);
    const highlighted = line.text.length ? highlightSql(line.text) : "&nbsp;";
    return `
      <div class="sql-line ${typeClass}" data-line-text="${escapeHtml(line.text)}">
        <span class="line-no">${escapeHtml(lineNo)}</span>
        <span class="line-code"><code class="hljs language-sql">${highlighted}</code></span>
      </div>
    `;
  }

  /**
   * @param {string} sourceSql
   * @param {string} targetSql
   */
  function buildSideBySideDiff(sourceSql, targetSql) {
    const source = splitSqlLines(sourceSql);
    const target = splitSqlLines(targetSql);

    const n = source.length;
    const m = target.length;
    const dp = Array.from({ length: n + 1 }, () => Array(m + 1).fill(0));

    for (let i = n - 1; i >= 0; i -= 1) {
      for (let j = m - 1; j >= 0; j -= 1) {
        if (source[i] === target[j]) {
          dp[i][j] = 1 + dp[i + 1][j + 1];
        } else {
          dp[i][j] = Math.max(dp[i + 1][j], dp[i][j + 1]);
        }
      }
    }

    /** @type {Array<{text: string, lineNo: number | null, type: "same"|"add"|"remove"|"empty"}>} */
    const left = [];
    /** @type {Array<{text: string, lineNo: number | null, type: "same"|"add"|"remove"|"empty"}>} */
    const right = [];

    let i = 0;
    let j = 0;

    while (i < n && j < m) {
      if (source[i] === target[j]) {
        left.push({ text: source[i], lineNo: i + 1, type: "same" });
        right.push({ text: target[j], lineNo: j + 1, type: "same" });
        i += 1;
        j += 1;
      } else if (dp[i + 1][j] >= dp[i][j + 1]) {
        left.push({ text: source[i], lineNo: i + 1, type: "remove" });
        right.push({ text: "", lineNo: null, type: "empty" });
        i += 1;
      } else {
        left.push({ text: "", lineNo: null, type: "empty" });
        right.push({ text: target[j], lineNo: j + 1, type: "add" });
        j += 1;
      }
    }

    while (i < n) {
      left.push({ text: source[i], lineNo: i + 1, type: "remove" });
      right.push({ text: "", lineNo: null, type: "empty" });
      i += 1;
    }

    while (j < m) {
      left.push({ text: "", lineNo: null, type: "empty" });
      right.push({ text: target[j], lineNo: j + 1, type: "add" });
      j += 1;
    }

    return { left, right };
  }

  /**
   * @param {HTMLElement} block
   * @param {string[]} patterns
   */
  function highlightSqlLines(block, patterns) {
    if (!patterns.length) {
      return;
    }

    const normalizedPatterns = patterns.map(normalizeForSearch).filter(Boolean);
    if (!normalizedPatterns.length) {
      return;
    }

    const lines = $$(".sql-line", block);
    let matched = false;

    lines.forEach((line) => {
      const raw = line.dataset.lineText ?? "";
      const normalized = normalizeForSearch(raw);
      if (normalizedPatterns.some((pattern) => normalized.includes(pattern))) {
        line.classList.add("line-emphasis");
        matched = true;
      }
    });

    if (!matched) {
      const tokenPatterns = normalizedPatterns
        .flatMap((pattern) => pattern.split(" "))
        .filter((token) => token.length >= 4);
      if (!tokenPatterns.length) {
        return;
      }
      lines.forEach((line) => {
        const normalized = normalizeForSearch(line.dataset.lineText ?? "");
        if (tokenPatterns.some((token) => normalized.includes(token))) {
          line.classList.add("line-emphasis");
        }
      });
    }
  }

  /**
   * @param {string | undefined} patternAttr
   */
  function parsePatternAttr(patternAttr) {
    return String(patternAttr || "")
      .split("||")
      .map((value) => value.trim())
      .filter(Boolean);
  }

  /**
   * @param {string} sql
   */
  function splitSqlLines(sql) {
    const normalized = String(sql || "").replace(/\r\n/g, "\n");
    return normalized.split("\n");
  }

  /**
   * @param {string} line
   */
  function highlightSql(line) {
    const text = String(line);
    if (!text.length) {
      return "&nbsp;";
    }

    if (window.hljs?.highlight) {
      try {
        const hasSqlLanguage =
          typeof window.hljs.getLanguage === "function" ? window.hljs.getLanguage("sql") : true;
        if (hasSqlLanguage) {
          return window.hljs.highlight(text, { language: "sql", ignoreIllegals: true }).value;
        }
        if (typeof window.hljs.highlightAuto === "function") {
          return window.hljs.highlightAuto(text).value;
        }
        return escapeHtml(text);
      } catch (_error) {
        return escapeHtml(text);
      }
    }

    return escapeHtml(text);
  }

  /**
   * @param {string} value
   */
  function normalizeForSearch(value) {
    return String(value)
      .toLowerCase()
      .replace(/[`\[\]'"(),.;]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  /**
   * @param {string} selector
   * @param {string} value
   */
  function setText(selector, value) {
    const element = $(selector);
    if (element) {
      element.textContent = value;
    }
  }

  /**
   * @param {string} text
   */
  function titleCase(text) {
    return String(text)
      .split("_")
      .join(" ")
      .split(" ")
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  }

  /**
   * @param {Array<string>} labels
   * @param {number} width
   * @param {number} height
   * @param {number} columns
   */
  function spreadCenters(labels, width, height, columns) {
    const rows = Math.ceil(labels.length / columns);
    const map = new Map();
    labels.forEach((label, index) => {
      const col = index % columns;
      const row = Math.floor(index / columns);
      const x = ((col + 1) / (columns + 1)) * width;
      const y = ((row + 1) / (rows + 1)) * height;
      map.set(label, { x, y });
    });
    return map;
  }

  /**
   * @param {string} hex
   * @param {number} alpha
   */
  function hexToRgba(hex, alpha) {
    const sanitized = hex.replace("#", "");
    const chunk = sanitized.length === 3 ? sanitized.split("").map((c) => c + c).join("") : sanitized;
    const int = Number.parseInt(chunk, 16);
    const red = (int >> 16) & 255;
    const green = (int >> 8) & 255;
    const blue = int & 255;
    return `rgba(${red}, ${green}, ${blue}, ${alpha.toFixed(3)})`;
  }

  /**
   * @param {string} raw
   */
  function escapeHtml(raw) {
    return String(raw ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }
})();
