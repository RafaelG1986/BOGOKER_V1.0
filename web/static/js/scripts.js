document.addEventListener('DOMContentLoaded', function() {
    // Inicializar DataTables si existe la tabla
    if (document.getElementById('leads-table')) {
        $('#leads-table').DataTable({
            "language": {
                "url": "//cdn.datatables.net/plug-ins/1.13.5/i18n/es-ES.json"
            },
            "order": [[0, "desc"]]
        });
    }
    
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
});