import { api } from "../../scripts/api.js";
import { app } from "../../scripts/app.js";
import { $el } from "../../scripts/ui.js";


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

function loadHljsCSS() {
  if (document.getElementById("hljs-style")) {
    return;
  }

  const style = document.createElement("style");
  style.id = "hljs-style";
  style.innerHTML = `
    .get-postition-style {
      display: flex-inline;
      position: absolute;
      left: 0px;
      top: 0px;
      width: 100%;
      height: 100%;
      font-size: 10px;
    }
    
    .get-postition-style pre {
      height: calc(100% - 2rem);
    }
    
    pre code.hljs {
      padding: 1.25em 0.5rem 0.5rem 0.5rem;
    }
    
    code.hljs {
      display: flex;
      flex: 1;
      border: 1px solid;
      border-radius: 0.25rem;
      border-color: var(--border-color);
      color: #abb2bf;
      background: #282c34;
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
  const transform = new DOMMatrix();

  transform
    .scaleSelf(elRect.width / ctx.canvas.width, elRect.height / ctx.canvas.height)
    .multiplySelf(ctx.getTransform())
    .translateSelf(MARGIN, MARGIN - 8 + y);

  return {
    position: 'absolute',
    transform: transform.toString(),
    transformOrigin: '0 0',
    maxWidth: `${widget_width - MARGIN * 2}px`,
    minHeight: `${node_height - 64 - MARGIN * 2}px`,
    maxHeight: `${node_height - 64 - MARGIN * 2}px`,    // we're assuming we have the whole height of the node
  };
}



const CDN_BASE_URL = 'https://cdnjs.cloudflare.com/ajax/libs/';
Promise.all([
  loadScript(`${CDN_BASE_URL}highlight.js/11.9.0/highlight.min.js`),
  loadScript(`${CDN_BASE_URL}highlight.js/11.9.0/languages/python.min.js`),
  loadCSS(`${CDN_BASE_URL}highlight.js/11.9.0/styles/atom-one-dark.min.css`),
  loadScript(`${CDN_BASE_URL}highlightjs-line-numbers.js/2.8.0/highlightjs-line-numbers.min.js`),
])
  .then(() => {
    app.registerNodeDef("Code", {
      name: "Code",
      category: "Shibiko",
      color: "#FFA800",
      input: {
        required: {
          code: ["STRING", { "forceInput": true, "multiline": true }],
        },
        optional: {
          lang: ["STRING", { default: "python" }],
          key: ["STRING", { default: "function" }],
        }
      },
      output: {
        code: ["STRING"],
      }
    });

    app.registerExtension({
      name: "ShibikoCodeDisplay",
      async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeType.comfyClass === "Code") {
          console.log('nodeType', nodeType);
          const orig_nodeCreated = nodeType.prototype.onNodeCreated;
          nodeType.prototype.onNodeCreated = function (node) {
            let widget = {
              type: "CODEBLOCK", // whatever
              name: "CODEBLOCK", // whatever
              draw(ctx, node, widget_width, y, widget_height) {
                Object.assign(this.html.style, get_position_style(ctx, widget_width, y, node.size[1])); // assign the required style when we are drawn
              },
            };

            const create_code_widget = (code = '# Waiting for code...', language = 'python') => {
              widget.html = $el('section', { className: 'get-postition-style' });
              const preBlock = $el('pre', {});
              const innerHTML = hljs.highlight(code, { language }).value;
              const codeBlock = $el('code', { className: 'language-python', innerHTML });
              preBlock.appendChild(codeBlock);
              widget.html.appendChild(preBlock);
              document.body.appendChild(widget.html);


              this.addCustomWidget(widget);
              hljs.highlightAll();
              hljs.initLineNumbersOnLoad();

              this.onRemoved = function () {
                widget.html.remove();
              };

              return widget;
            };

            orig_nodeCreated?.apply(this, arguments);
            loadHljsCSS();

            api.addEventListener('code', (event) => {
              console.log('API EVENT', event);
              const { code, id, lang } = event.detail;
              // if (id === nodeType.id) {
                if (widget) {
                  widget.html.remove();
                }
                widget = create_code_widget(code, lang);
              // }
            });

            let code = '# Waiting for code...';
            let lang = 'python';
            widget = create_code_widget(code, lang);
            this.serialize_widgets = false;
          }

          const orig_onExecuted = nodeType.prototype.onExecuted;
        }
      },
    });
  });
