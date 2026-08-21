(() => {
  "use strict";

  const STORAGE_KEY = "calm-calculator-history-v1";
  const expressionInput = document.querySelector("#expression");
  const resultOutput = document.querySelector("#result");
  const message = document.querySelector("#calculation-message");
  const keypad = document.querySelector(".keypad");
  const copyButton = document.querySelector("#copy-result");
  const historyList = document.querySelector("#history-list");
  const emptyHistory = document.querySelector("#empty-history");
  const clearHistoryButton = document.querySelector("#clear-history");

  let currentResult = "";
  let previewTimer;
  let requestCounter = 0;
  let history = loadHistory();

  function loadHistory() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
      return Array.isArray(saved) ? saved.slice(0, 10) : [];
    } catch (_error) {
      return [];
    }
  }

  function saveHistory() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch (_error) {
      // A private browser can block storage; calculation should still work.
    }
  }

  function renderHistory() {
    historyList.replaceChildren();
    emptyHistory.hidden = history.length > 0;
    clearHistoryButton.hidden = history.length === 0;

    history.forEach((entry) => {
      const item = document.createElement("li");
      item.className = "history-item";
      const button = document.createElement("button");
      button.type = "button";
      button.className = "history-button";
      button.dataset.expression = entry.expression;
      button.setAttribute("aria-label", `Reuse ${entry.expression}, result ${entry.result}`);

      const expression = document.createElement("span");
      expression.className = "history-expression";
      expression.textContent = prettyExpression(entry.expression);
      const result = document.createElement("span");
      result.className = "history-result";
      result.textContent = `= ${entry.result}`;

      button.append(expression, result);
      item.append(button);
      historyList.append(item);
    });
  }

  function prettyExpression(expression) {
    return expression.replaceAll("*", "×").replaceAll("/", "÷").replaceAll("-", "−");
  }

  function normalizeExpression(expression) {
    return expression
      .replaceAll("×", "*")
      .replaceAll("÷", "/")
      .replaceAll("−", "-")
      .trim();
  }

  function setMessage(text, state = "") {
    message.textContent = text;
    message.className = `calculation-message${state ? ` ${state}` : ""}`;
  }

  function setResult(result) {
    currentResult = result;
    resultOutput.textContent = result || "0";
    copyButton.disabled = !result;
  }

  function calculateLocally(expression) {
    if (expression.length > 1000) throw new Error("That expression is too long.");

    let position = 0;
    let operations = 0;

    function fail(message = "Invalid arithmetic expression.") {
      throw new Error(message);
    }

    function skipSpaces() {
      while (/\s/.test(expression[position] || "")) position += 1;
    }

    function consume(character) {
      skipSpaces();
      if (expression[position] !== character) return false;
      position += 1;
      return true;
    }

    function countOperation() {
      operations += 1;
      if (operations > 1000) fail("That expression is too complex.");
    }

    function parseNumber() {
      skipSpaces();
      const match = expression.slice(position).match(/^(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?/);
      if (!match) fail();
      position += match[0].length;
      return Number(match[0]);
    }

    function parsePrimary(depth) {
      if (depth > 200) fail("That expression is too deeply nested.");
      if (consume("(")) {
        const value = parseExpression(depth + 1);
        if (!consume(")")) fail("A closing parenthesis is missing.");
        return value;
      }
      return parseNumber();
    }

    function parseUnary(depth) {
      if (consume("+")) {
        countOperation();
        return parseUnary(depth + 1);
      }
      if (consume("-")) {
        countOperation();
        return -parseUnary(depth + 1);
      }
      return parsePrimary(depth);
    }

    function parseTerm(depth) {
      let value = parseUnary(depth);
      while (true) {
        if (consume("*")) {
          countOperation();
          value *= parseUnary(depth);
        } else if (consume("/")) {
          countOperation();
          const divisor = parseUnary(depth);
          if (divisor === 0) fail("Cannot divide by zero.");
          value /= divisor;
        } else {
          return value;
        }
      }
    }

    function parseExpression(depth = 0) {
      let value = parseTerm(depth);
      while (true) {
        if (consume("+")) {
          countOperation();
          value += parseTerm(depth);
        } else if (consume("-")) {
          countOperation();
          value -= parseTerm(depth);
        } else {
          return value;
        }
      }
    }

    if (!expression.trim()) fail("Enter something to calculate.");
    const value = parseExpression();
    skipSpaces();
    if (position !== expression.length) fail("Use only numbers, parentheses, +, −, ×, and ÷.");
    if (!Number.isFinite(value)) return value > 0 ? "∞" : "−∞";
    if (Object.is(value, -0)) return "0";
    return Number.parseFloat(value.toPrecision(15)).toString();
  }

  async function requestCalculation(expression, { final = false } = {}) {
    const requestId = ++requestCounter;

    try {
      // Yield once so rapid input can supersede a stale live calculation.
      await Promise.resolve();
      const result = calculateLocally(expression);

      if (requestId !== requestCounter) return null;
      setResult(result);
      setMessage(final ? "Calculation saved to your tape" : "Live result", "success");
      return result;
    } catch (error) {
      if (requestId !== requestCounter) return null;
      if (final) {
        setMessage(error.message || "Check that expression and try again.", "error");
      } else {
        setResult("");
        setMessage("Keep going…");
      }
      return null;
    }
  }

  function schedulePreview() {
    window.clearTimeout(previewTimer);
    const expression = normalizeExpression(expressionInput.value);

    if (!expression) {
      requestCounter += 1;
      setResult("");
      setMessage("Ready when you are");
      return;
    }

    const lastCharacter = expression.at(-1);
    if ("+-*/.(".includes(lastCharacter)) {
      requestCounter += 1;
      setResult("");
      setMessage("Keep going…");
      return;
    }

    setMessage("Working it out…");
    previewTimer = window.setTimeout(() => requestCalculation(expression), 260);
  }

  function addToHistory(expression, result) {
    history = history.filter((entry) => entry.expression !== expression);
    history.unshift({ expression, result });
    history = history.slice(0, 10);
    saveHistory();
    renderHistory();
  }

  async function calculate() {
    window.clearTimeout(previewTimer);
    const expression = normalizeExpression(expressionInput.value);
    if (!expression) {
      setMessage("Enter something to calculate.", "error");
      expressionInput.focus();
      return;
    }

    setMessage("Calculating…");
    const result = await requestCalculation(expression, { final: true });
    if (result !== null) addToHistory(expression, result);
  }

  function insertValue(value) {
    const start = expressionInput.selectionStart ?? expressionInput.value.length;
    const end = expressionInput.selectionEnd ?? expressionInput.value.length;
    const existing = expressionInput.value;
    let insertion = value;

    if ("+-*/".includes(value)) {
      const before = existing.slice(0, start).trimEnd();
      const last = before.at(-1);
      if (last && "+-*/".includes(last)) {
        const operatorIndex = existing.slice(0, start).lastIndexOf(last);
        expressionInput.value = `${existing.slice(0, operatorIndex)}${value}${existing.slice(end)}`;
        expressionInput.setSelectionRange(operatorIndex + 1, operatorIndex + 1);
        schedulePreview();
        expressionInput.focus();
        return;
      }
      insertion = ` ${value} `;
    }

    expressionInput.value = `${existing.slice(0, start)}${insertion}${existing.slice(end)}`;
    const nextPosition = start + insertion.length;
    expressionInput.setSelectionRange(nextPosition, nextPosition);
    schedulePreview();
    expressionInput.focus();
  }

  function insertParenthesis() {
    const beforeCursor = expressionInput.value.slice(0, expressionInput.selectionStart ?? undefined);
    const opens = (beforeCursor.match(/\(/g) || []).length;
    const closes = (beforeCursor.match(/\)/g) || []).length;
    const previous = beforeCursor.trim().at(-1);
    const shouldClose = opens > closes && previous && /[\d.)]/.test(previous);
    insertValue(shouldClose ? ")" : "(");
  }

  function backspace() {
    const start = expressionInput.selectionStart ?? expressionInput.value.length;
    const end = expressionInput.selectionEnd ?? expressionInput.value.length;
    if (start !== end) {
      expressionInput.value = expressionInput.value.slice(0, start) + expressionInput.value.slice(end);
      expressionInput.setSelectionRange(start, start);
    } else if (start > 0) {
      expressionInput.value = expressionInput.value.slice(0, start - 1) + expressionInput.value.slice(start);
      expressionInput.setSelectionRange(start - 1, start - 1);
    }
    schedulePreview();
    expressionInput.focus();
  }

  function clearCalculator() {
    window.clearTimeout(previewTimer);
    requestCounter += 1;
    expressionInput.value = "";
    setResult("");
    setMessage("Ready when you are");
    expressionInput.focus();
  }

  function toggleSign() {
    const expression = normalizeExpression(expressionInput.value);
    if (!expression) {
      insertValue("-");
      return;
    }
    expressionInput.value = expression.startsWith("-(") && expression.endsWith(")")
      ? expression.slice(2, -1)
      : `-(${expression})`;
    expressionInput.setSelectionRange(expressionInput.value.length, expressionInput.value.length);
    schedulePreview();
    expressionInput.focus();
  }

  function flashKey(selector) {
    const key = document.querySelector(selector);
    if (!key) return;
    key.classList.add("pressed");
    window.setTimeout(() => key.classList.remove("pressed"), 100);
  }

  keypad.addEventListener("click", (event) => {
    const key = event.target.closest("button");
    if (!key) return;

    if (key.dataset.value) insertValue(key.dataset.value);
    if (key.dataset.action === "clear") clearCalculator();
    if (key.dataset.action === "backspace") backspace();
    if (key.dataset.action === "parentheses") insertParenthesis();
    if (key.dataset.action === "sign") toggleSign();
    if (key.dataset.action === "equals") calculate();
  });

  expressionInput.addEventListener("input", schedulePreview);
  expressionInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      flashKey('[data-action="equals"]');
      calculate();
    } else if (event.key === "Escape") {
      event.preventDefault();
      flashKey('[data-action="clear"]');
      clearCalculator();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (document.activeElement === expressionInput || event.metaKey || event.ctrlKey || event.altKey) return;
    if (/^[0-9.+\-*/()]$/.test(event.key)) {
      event.preventDefault();
      insertValue(event.key);
      flashKey(`[data-value="${CSS.escape(event.key)}"]`);
    } else if (event.key === "Enter") {
      event.preventDefault();
      calculate();
      flashKey('[data-action="equals"]');
    } else if (event.key === "Backspace") {
      event.preventDefault();
      backspace();
      flashKey('[data-action="backspace"]');
    }
  });

  historyList.addEventListener("click", (event) => {
    const button = event.target.closest(".history-button");
    if (!button) return;
    expressionInput.value = button.dataset.expression;
    expressionInput.setSelectionRange(expressionInput.value.length, expressionInput.value.length);
    schedulePreview();
    expressionInput.focus();
  });

  clearHistoryButton.addEventListener("click", () => {
    history = [];
    saveHistory();
    renderHistory();
  });

  copyButton.addEventListener("click", async () => {
    if (!currentResult) return;
    try {
      await navigator.clipboard.writeText(currentResult);
      const label = copyButton.querySelector("span");
      label.textContent = "Copied";
      window.setTimeout(() => { label.textContent = "Copy"; }, 1200);
    } catch (_error) {
      setMessage("Could not access the clipboard.", "error");
    }
  });

  renderHistory();
})();
