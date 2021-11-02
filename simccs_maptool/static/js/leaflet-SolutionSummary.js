
L.Control.SolutionSummary = L.Control.extend({
    summaries: new Map(),
    el: null,

    onAdd(map) {
        const card = this.el = document.createElement('div');
        card.classList.add("card");
        const cardHeader = document.createElement('div');
        cardHeader.classList.add('card-header', 'd-flex', 'justify-content-between');
        const cardHeaderTitle = document.createElement('div');
        cardHeaderTitle.textContent = "Solution Summary";
        cardHeader.appendChild(cardHeaderTitle);
        // <i class="fas fa-angle-up"></i>
        const icon = document.createElement('i');
        icon.classList.add('fas', 'fa-angle-up', 'ml-3', 'text-muted');
        const iconBaseStyle = "cursor: pointer; font-size: 1.4rem; transition: transform 0.3s;";
        icon.style = iconBaseStyle;
        cardHeader.appendChild(icon);
        card.appendChild(cardHeader);
        const collapsible = document.createElement('div');
        collapsible.classList.add('collapse', 'show');
        const cardBody = document.createElement('div');
        cardBody.classList.add("card-body");
        collapsible.appendChild(cardBody);
        card.appendChild(collapsible);

        let collapsed = false;
        icon.addEventListener("click", () => {
          if (collapsed) {
            $(collapsible).collapse("show");
            icon.style = iconBaseStyle;
          } else {
            $(collapsible).collapse("hide");
            icon.style = iconBaseStyle + " transform: rotate(-180deg);";
          }
          collapsed = !collapsed;
        });
        L.DomEvent.disableClickPropagation(card);
        L.DomEvent.disableScrollPropagation(card);
        return card;
    },

    onRemove(map) {
        // Nothing to do here
    },

    addSolutionSummary(solutionLabel, solutionSummary) {
        this.summaries.set(solutionLabel, solutionSummary);
        this.render();
    },

    removeSolutionSummary(solutionLabel) {
        this.summaries.delete(solutionLabel);
        this.render();
    },

    render() {
        const cardBody = this.el.querySelector('.card-body');
        this.generateTable(cardBody);
    },

    generateTable(container) {
        const labels = [...this.summaries.keys()];
        const summaries = [...this.summaries.values()];
        container.innerHTML = `
            <table class="table table-sm">
                <tbody>
                <tr class="table-secondary">
                        <th scope="row">Experiment</th>
                        ${labels.map(k => `<td>${k}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Sources</th>
                        ${summaries.map(s => s.numOpenedSources).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Sinks</th>
                        ${summaries.map(s => s.numOpenedSinks).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">MtCO<sub>2</sub> Stored</th>
                        ${summaries.map(s => s.targetCaptureAmount.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Edges</th>
                        ${summaries.map(s => s.numEdgesOpened).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Project Length (yr)</th>
                        ${summaries.map(s => s.projectLength).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr class="table-secondary">
                        <th scope="row">Total Cost ($m/yr)</th>
                        ${labels.map(k => `<td></td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Capture</th>
                        ${summaries.map(s => s.totalCaptureCost.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Transport</th>
                        ${summaries.map(s => s.totalTransportCost.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Storage</th>
                        ${summaries.map(s => s.totalStorageCost.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Total</th>
                        ${summaries.map(s => s.totalCost.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr class="table-secondary">
                        <th scope="row">Unit Cost ($/tCO<sub>2</sub>)</th>
                        ${labels.map(k => `<td></td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Capture</th>
                        ${summaries.map(s => s.unitCaptureCost.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Transport</th>
                        ${summaries.map(s => s.unitTransportCost.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Storage</th>
                        ${summaries.map(s => s.unitStorageCost.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Total</th>
                        ${summaries.map(s => s.unitTotalCost.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                </tbody>
            </table>
        `;
    }

});

L.control.solutionSummary = function(opts) {
    return new L.Control.SolutionSummary(opts);
}
