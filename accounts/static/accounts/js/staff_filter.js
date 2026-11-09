$(document).ready(function () {

    // default filter values
    let roleFilter = "all";
    let statusFilter = "all";
    let branchFilter = "all";


    // Apply all active filters
    function applyFilters() {

        let visibleCount = 0  // initialize visible cards to 0

        $(".staff-card").each(function () {

            const role = $(this).data("role");

            const status = $(this).data("status");

            const branch = String($(this).data("branch"));

            let visible = true;

            // Hide cards that don't match selected role
            if (roleFilter !== "all" && role !== roleFilter) {
                visible = false;
            }

            // Hide cards that don't match selected status
            if (statusFilter !== "all" && status !== statusFilter) {
                visible = false;
            }

            // Hide cards that don't match selected branch
            if (branchFilter !== "all" && branch !== branchFilter) {
                visible = false;
            }

            // Show or hide cards based on selected filters
            if (visible) {
                  visibleCount++;
            }

            $(this).toggle(visible);
        });

        if (visibleCount === 0) {  // display 0 results feedback
            $("#no-results").show();

        }else {
            $("#no-results").hide();  // hide 0 results feedback
       }
    }



    // Handle role and status filter button clicks
    $(".filter-btn").click(function () {

        $(".filter-btn").removeClass("btn-primary active").addClass("btn-outline-primary"); // Remove highlighting from all filter buttons

        $(this).removeClass("btn-outline-primary").addClass("btn-primary active");  // Highlight selected button

        const filter = $(this).data("filter");


        if (filter === "admin") {  // Update role filter
            roleFilter =  "Administrator";

        }else if (filter === "cashier") {
            roleFilter = "Cashier";

        }else if (filter === "active") { // Update status filter
            statusFilter = "active";

        }else if (filter === "inactive") {
            statusFilter = "inactive";

        }else if (filter === "all") { // Reset all filters

            roleFilter = "all";

            statusFilter = "all";

            branchFilter = "all";

            $("#branch-filter").val("all");
        }

        applyFilters(); // Apply all selected filters

    });

    $("#branch-filter").change(function () { // Handle branch dropdown changes
        branchFilter = $(this).val();
        applyFilters();

    });

});