import { create_show_code_widget, setMiniumSize, update_show_code_widget } from './widget.js';

function loadStoredOutputs(node) {
  let code = '# Waiting for code...';
  let language = 'python';
  let control = null;

  try {
    const { link } = node.inputs[0];
    const { origin_id, origin_slot } = app.graph.links[link];
    const origin_node = app.graph.getNodeById(origin_id);

    // output_values is created by storeAnyNodeOutputs in store-outputs.js
    control = origin_node.outputs_values[origin_slot];
    code = control && control.function + '\n\n' || code;
  } catch(e) {}

  return { code, language, control };
}

/**
 * Add a callback to the show widget
 * inputs[0] is the control input
 */
function createShowWidgetCallback(node) {
  node.widgets[0].callback = function (value) {
    const control = node.widgets[1].value;
    node.widgets_values[0] = value;

    if (!control) return;
    update_show_code_widget(
      value === 'code' ? control.function : JSON.stringify(control, null, 4),
      value === 'code' ? 'python' : 'json',
      node.id
    );
  };
}

export function showCode(node) {
  const { code, language, control } = loadStoredOutputs(node);
  const widget = create_show_code_widget(code, language, node.id);
  widget.value = control;
  node.widgets_values = ['code', control];

  setMiniumSize(node, 300, 200);
  hljs.highlightAll();
  hljs.initLineNumbersOnLoad();

  // Found out that there is node.addDOMWidget, but this is working...
  node.addCustomWidget(widget);
  createShowWidgetCallback(node);

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
