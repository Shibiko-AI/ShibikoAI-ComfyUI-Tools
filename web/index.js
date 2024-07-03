import { api } from '../../scripts/api.js';
import { app } from '../../scripts/app.js';
import { $el } from '../../scripts/ui.js';

function loadCSS(url) {
  return new Promise((resolve, reject) => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = url;
    link.onload = resolve;
    link.onerror = reject;
    document.head.appendChild(link);
  });
}

function loadHljsStyleBlock() {
  if (document.getElementById('hljs-style')) {
    return;
  }

  const style = document.createElement('style');
  style.id = 'hljs-style';
  style.innerHTML = `
    .get-position-style {
      left: 0px;
      top: 0px;
      width: 100%;
      height: 100%;
      font-size: 10px;
    }
    
    .get-position-style pre {
      height: calc(100% - 2rem);
    }
    
    pre code.hljs, .any-node-input {
      padding: 0.75em 0.5rem 0.5rem 0.5rem;
    }
    
    code.hljs, .any-node-input {
      display: flex;
      flex: 1;
      border: 1px solid;
      border-radius: 0.25rem;
      border-color: var(--border-color);
      color: #abb2bf;
      background: #282c34 !important;
      height: 100%;
    }
    
    .hljs-ln-numbers {
      -webkit-touch-callout: none;
      -webkit-user-select: none;
      -khtml-user-select: none;
      -moz-user-select: none;
      -ms-user-select: none;
      user-select: none;
  
      text-align: right;
      color: #5c6370;
      border-right: 1px solid #5c6370;
      vertical-align: top;
      padding-right: 8px !important;
    }
    
    .hljs-ln-code {
      padding-left: 8px !important;
    }
    
    pre code {
    --scrollbar-bg: #282c34;
    --thumb-bg: #4b5263;
    --thumb-bg-hover: #5c6370;
  
    overflow: auto;

    scrollbar-width: thin;
      scrollbar-color: var(--thumb-bg) var(--scrollbar-bg);
    }
    
    pre code::-webkit-scrollbar {
      width: 12px;
      height: 12px;
    }
    
    pre code::-webkit-scrollbar-track {
      background: var(--scrollbar-bg);
    }
    
    pre code::-webkit-scrollbar-thumb {
      background-color: var(--thumb-bg);
      border-radius: 6px;
      border: 3px solid var(--scrollbar-bg);
    }
    
    pre code::-webkit-scrollbar-thumb:hover {
      background-color: var(--thumb-bg-hover);
    }
    
    pre code {
      scrollbar-width: thin;
      scrollbar-color: var(--thumb-bg) var(--scrollbar-bg);
    }
    
    pre {
      position: relative;
    }
    
    .copy-button {
      position: absolute;
      top: 0.8rem;
      right: 0.1rem;
      padding: 0.5rem;
      margin: 0;
      background-color: rgba(40, 44, 52, 0.5);
      border: none;
      border-radius: 0.25rem;
      cursor: pointer;
      transition: background-color 0.3s ease;
      font-size: 0rem;
    }
    
    .copy-button:hover {
      background-color: rgba(92, 99, 112, 0.5);
    }
    
    .copy-button:hover svg {
      transform: scale(1.1);
    }
    
    @keyframes flash-green {
      0%, 100% {
        background-color: rgba(40, 44, 52, 0.5);
        border-color: rgba(40, 44, 52, 0.5);
      }
      50% {
        background-color: rgba(80, 200, 120, 0.5);
        border-color: rgba(80, 200, 120, 0.5);
      }
    }
    
    @keyframes flash-svg {
      0% {
        transform: scale(1);
      }
      50% {
        transform: scale(1.4);
      }
      100% {
        transform: scale(1.1);
      }
    }
    
    .flash {
      animation: flash-green 1s ease;
      outline: none;
    }
    
    .flash svg {
      animation: flash-svg 1s ease;
    }
    
    .copy-button:active {
      transform: scale(0.9);
    }
    
    .copy-button svg {
      width: 1rem;
      height: 1rem;
      stroke: #abb2bf;
    }
  `;
  document.body.appendChild(style);
}

function loadScript(url) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = url;
    script.onload = () => resolve(window);
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

function get_position_style(ctx, widget_width, y, node_height) {
  const MARGIN = 16;

  /* Create a transform that deals with all the scrolling and zooming */
  const elRect = ctx.canvas.getBoundingClientRect();
  const initialTransform = ctx.getTransform();

  const transform = new DOMMatrix()
    .scaleSelf(elRect.width / ctx.canvas.width, elRect.height / ctx.canvas.height)
    .multiplySelf(initialTransform)
    .translateSelf(MARGIN, y - MARGIN / 1.5);

  return {
    position: 'absolute',
    transform: transform.toString(),
    transformOrigin: '0 0',
    maxWidth: `${widget_width - MARGIN * 2}px`,
    minHeight: `${node_height - 56 - MARGIN / 2.5}px`,
    maxHeight: `${node_height - 56 - MARGIN / 2.5}px`,    // we're assuming we have the whole height of the node
  };
}

function setMiniumSize(node, width, height) {
  if (node.size[0] < width) {
    node.size[0] = width;
  }

  if (node.size[1] < height) {
    node.size[1] = height;
  }
}

function create_code_widget(code = '# Waiting for code...', language = 'python', id = 0) {
  const listener = api.addEventListener(`any-node-show-code-${id}`, (event) => {
    const { code, control, language, unique_id } = event.detail;
    widget.value = control;
    widget.language = language;
    if (!app.graph.getNodeById(unique_id).widgets_values) {
      app.graph.getNodeById(unique_id).widgets_values = [];
    }
    app.graph.getNodeById(unique_id).widgets_values[1] = control;
    update_code_widget(code, language, unique_id);
  });

  /** @type {IWidget} */
  let widget = {
    node: id,
    type: 'CODE',
    name: 'CODE',
    html: $el('section', { className: 'get-position-style' }),
    language: 'python',
    copy() {
      if (!widget.value) {
        return navigator.clipboard.writeText(code);
      }

      if (this.language === 'python') {
        return navigator.clipboard.writeText(widget.value.function);
      }

      if (this.language === 'json') {
        return navigator.clipboard.writeText(JSON.stringify(widget.value, null, 4));
      }
    },
    draw(ctx, node, widget_width, y) {
      Object.assign(this.html.style, get_position_style(ctx, widget_width, y, node.size[1]));
    },
    onRemoved() {
      api.removeEventListener(`any-node-show-code-${id}`, listener);
    },
  };

  const highlightedCode = hljs.highlight(code, { language }).value;
  widget.html.innerHTML = `
    <pre>
      <code id="any-node-show-code-${id}" class="language-python"></code>
      <button class="copy-button" aria-label="Copy code">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
      </button>
    </pre>
  `;
  widget.html.querySelector(`#any-node-show-code-${id}`).innerHTML = highlightedCode;
  const codeEl = widget.html.querySelector('code');
  const button = widget.html.querySelector('.copy-button');
  button.addEventListener('click',
    () => {
      widget.copy();
      button.classList.remove('flash');
      codeEl.classList.remove('flash');
      setTimeout(() => button.classList.add('flash') || codeEl.classList.add('flash'), 0);
    }
  );
  document.body.appendChild(widget.html);

  return widget;
}

function update_code_widget (code = '# Waiting for code...', language = 'python', id = 0) {
  const el = document.getElementById(`any-node-show-code-${id}`);
  el.innerHTML = hljs.highlight(code + '\n\n', { language }).value;
  hljs.initLineNumbersOnLoad();
}

function highlight() {
  try {
    hljs.highlightAll();
    hljs.initLineNumbersOnLoad();
  } catch (e) {}
}

const CDN_BASE_URL = 'https://cdnjs.cloudflare.com/ajax/libs';
Promise.all([
  loadScript(`${CDN_BASE_URL}/highlight.js/11.9.0/highlight.min.js`),
  loadCSS(`${CDN_BASE_URL}/highlight.js/11.9.0/styles/atom-one-dark.min.css`),
])
  .then(() => loadScript(`${CDN_BASE_URL}/highlightjs-line-numbers.js/2.8.0/highlightjs-line-numbers.min.js`))
  .then(() => {
    // No vulnerabilities here so suppress the warning
    hljs.configure({ ignoreUnescapedHTML: true });

    app.registerExtension({
      name: 'AnyNode',
      async sleep (ms=0) {
        return new Promise(resolve => setTimeout(resolve, ms));
      },
      async nodeCreated(node) {
        await this.sleep(0); // Wait for node object to be updated
        if (node.type.includes('AnyNode')) {
          node.bgcolor = "#512222";

          (node.inputs || []).forEach(input => {
            if (input.name === 'control') {
              input.color_on = "#f495bf";
            }
          });

          (node.outputs || []).forEach(output => {
            if (output.name === 'control') {
              output.color_on = "#f495bf";
            }
          });

          (node.widgets || []).forEach(widget => {
            if (widget.type === 'customtext') {
              widget.inputEl.classList.add('any-node-input');
            }
          });

          if (node.type !== 'AnyNodeShowCode') {
            node.onExecuted = function (event) {
              node.outputs_values = node.outputs_values || [];
              node.outputs.forEach((output, index) => {
                node.outputs_values[index] = event[output.name] && event[output.name][0] || undefined;
              });
            };
          }
        }

        if (node.type === 'AnyNodeShowCode') {
          let code = '# Waiting for code...';
          let language = 'python';
          let control = null;

          try {
            const { link } = node.inputs[0];
            const { origin_id, origin_slot } = app.graph.links[link];
            const origin_node = app.graph.getNodeById(origin_id);

            control = origin_node.outputs_values[origin_slot];
            code = control && control.function + '\n\n' || code;
          } catch(e) {}

          const widget = create_code_widget(code, language, node.id);
          widget.value = control;
          node.widgets_values = ['code', control];

          setMiniumSize(node, 300, 200);
          loadHljsStyleBlock();
          highlight();

          // Just found out that there is node.addDOMWidget, but this is working...
          node.addCustomWidget(widget);

          // Add a callback to the show widget
          node.widgets[0].callback = function (value) {
            const control = node.widgets[1].value;
            node.widgets_values[0] = value;

            if (!control) return;
            update_code_widget(
              value === 'code' ? control.function : JSON.stringify(control, null, 4),
              value === 'code' ? 'python' : 'json',
              node.id
            );
          };

          const onDrawForeground = node.onDrawForeground;
          node.onDrawForeground = function(ctx, graph) {
            onDrawForeground.apply(this, arguments);
            widget.html.style.display = this.flags.collapsed ? 'none' : 'block';
            if (this.flags.collapsed) {
              widget.html.querySelector('code').classList.remove('flash');
              widget.html.querySelector('.copy-button').classList.remove('flash');
            }
          };

          const onRemoved = node.onRemoved;
          node.onRemoved = function () {
            onRemoved.apply(this, arguments);
            widget.html.remove();
          };

          const onResize = node.onResize;
          node.onResize = function(size) {
            onResize.apply(this, arguments);
            setMiniumSize(node, 300, 200);
          };
        }
      },
    });
  });
