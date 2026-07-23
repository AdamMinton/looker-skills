// harness/mocks.js
window.looker = {
  plugins: {
    visualizations: {
      add: function (viz) {
        console.log(`Registering visualization: ${viz.id}`);
        // Add required methods to the viz object itself as Looker does
        viz.clearErrors = function () { console.log('Errors cleared'); };
        viz.addError = function (e) { console.error('Error added:', e); };
        this[viz.id] = viz;
        // Make it available as currentViz for legacy harness support if needed
        window.currentViz = viz;
      },
    },
  },
  // Simplified trigger for events
  trigger: function (event, args) {
    console.log(`Looker Event: ${event}`, args);
  }
};

// Mock the LookerCharts utility library required by hello_world.js
window.LookerCharts = {
  Utils: {
    htmlForCell: (cell) => {
      // Basic mock: just return the escaped value
      return cell.value ? String(cell.value) : "";
    },
    textForCell: (cell) => cell.value,
  },
};