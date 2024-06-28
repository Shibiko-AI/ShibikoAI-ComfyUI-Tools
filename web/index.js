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

function loadScript(url) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = url;
    script.onload = () => resolve(window);
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

/*
A method that returns the required style for the html
*/
function get_position_style(ctx, widget_width, y, node_height) {
  const MARGIN = 16;  // the margin around the html element

  /* Create a transform that deals with all the scrolling and zooming */
  const elRect = ctx.canvas.getBoundingClientRect();
  const transform = new DOMMatrix()
    .scaleSelf(elRect.width / ctx.canvas.width, elRect.height / ctx.canvas.height)
    .multiplySelf(ctx.getTransform())
    .translateSelf(MARGIN, MARGIN - 8 + y);

  return {
    position: 'absolute',
    transform: transform,
    transformOrigin: '0 0',
    maxWidth: `${widget_width - MARGIN * 2}px`,
    minHeight: `${node_height - 64 - MARGIN * 2}px`,
    maxHeight: `${node_height - 64 - MARGIN * 2}px`,    // we're assuming we have the whole height of the node
  };
}

const CDN_BASE_URL = 'https://cdnjs.cloudflare.com/ajax/libs/';
// loadScript('https://cdn.jsdelivr.net/npm/marked/marked.min.js')
Promise.all([
  loadScript(`${CDN_BASE_URL}remarkable/2.0.1/remarkable.min.js`),
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
          const orig_nodeCreated = nodeType.prototype.onNodeCreated;
          nodeType.prototype.onNodeCreated = function (node) {
            orig_nodeCreated?.apply(this, arguments);
            const md = new remarkable.Remarkable({
              html:         false,        // Enable HTML tags in source
              xhtmlOut:     false,        // Use '/' to close single tags (<br />)
              breaks:       true,        // Convert '\n' in paragraphs into <br>
              langPrefix:   'language-',  // CSS language prefix for fenced blocks

              // Enable some language-neutral replacement + quotes beautification
              typographer:  false,

              // Double + single quotes replacement pairs, when typographer enabled,
              // and smartquotes on. Set doubles to '«»' for Russian, '„“' for German.
              quotes: '“”‘’',

              // Highlighter function. Should return escaped HTML,
              // or '' if the source string is not changed
              highlight(str, lang) {
                if (lang && hljs.getLanguage(lang)) {
                  try {
                    return hljs.highlight(lang, str).value;
                  } catch (error) {
                    console.error(error)
                  }
                }

                try {
                  return hljs.highlightAuto(str).value;
                } catch (error) {
                  console.error(error)
                }

                return ''; // use external default escaping
              }
            });

            const widget = {
              type: "CODEBLOCK", // whatever
              name: "CODEBLOCK-" + nodeData.id, // whatever
              draw(ctx, node, widget_width, y, widget_height) {
                Object.assign(this.code.style, get_position_style(ctx, widget_width, y, node.size[1])); // assign the required style when we are drawn
              },
            };

            // Create a style block
            const style = document.createElement("style");
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

            const code = `
def generated_function(input_data_1=None, input_data_2=None):
    def apply_mask(image_tensor, mask_tensor):
        # Ensure both tensors are of appropriate shape and type
        assert len(image_tensor.shape) == 4 and image_tensor.shape[-1] == 3, \\
            "Image tensor must be of shape (batch, width, height, 3)"
        assert len(mask_tensor.shape) == 3, \\
            "Mask tensor must be of shape (batch, width, height)"

        # Create an alpha channel based on the mask
        alpha_channel = (mask_tensor > 0).float()

        # Expand the mask tensor to match image tensor dimensions
        alpha_channel = alpha_channel.unsqueeze(-1).expand_as(image_tensor)

        # Apply the mask to the image tensor
        image_with_alpha = image_tensor * alpha_channel

        return image_with_alpha

    output_image = apply_mask(input_data_1, input_data_2)
    return output_image
            `.trimStart();

            const innerHTML = md.render('```python\n' + code + '\n```\n');
            console.log('innerHTML', innerHTML);
            widget.code = $el("section", { className: 'get-postition-style', innerHTML });
            document.body.appendChild(widget.code);


            this.addCustomWidget(widget);
            hljs.highlightAll();
            hljs.initLineNumbersOnLoad();
            this.onRemoved = function () {
              widget.inputEl.remove();
            };
            this.serialize_widgets = false;

          }
        }
      }
    });
  });

function garbage() {
  if (nodeData.name === "Code") {
    const origOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      origOnNodeCreated?.apply(this, arguments);

      const widget = {
        type: "CODE_DISPLAY",
        name: "code_display",
        draw(ctx, node, widget_width, y, widget_height) {
          Object.assign(this.codeElement.style, {
            position: 'absolute',
            left: `${node.pos[0]}px`,
            top: `${node.pos[1] + y}px`,
            width: `${widget_width}px`,
            height: `${widget_height}px`,
          });
        },
      };

      // Create the code display element
      widget.codeElement = document.createElement("pre");
      widget.codeElement.className = "language-python";
      widget.codeElement.style.margin = "0";
      widget.codeElement.style.padding = "10px";
      widget.codeElement.style.backgroundColor = "#f0f0f0";
      widget.codeElement.style.borderRadius = "5px";
      widget.codeElement.style.overflow = "auto";
      const codeContent = document.createElement("code");
      widget.codeElement.appendChild(codeContent);
      document.body.appendChild(widget.codeElement);

      this.addCustomWidget(widget);
      this.onRemoved = function () {
        widget.codeElement.remove();
      };
      this.serialize_widgets = false;

      // Update the code display when connections change
      this.onConnectionsChange = function (slot) {
        if (slot === 0) {  // Assuming 'code' is the first input
          const inputLink = this.inputs[0].link;
          if (inputLink) {
            const inputNode = app.graph.getNodeById(inputLink.origin_id);
            const value = inputNode.outputs[inputLink.origin_slot].value;
            if (value) {
              codeContent.textContent = value;
              Prism.highlightElement(codeContent);
            }
          }
        }
      };
    };
  }
}
