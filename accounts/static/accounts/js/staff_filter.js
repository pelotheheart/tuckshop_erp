$(document).ready(function () {

    $(".filter-btn").click(function () { // Handle filter button clicks

        $(".filter-btn").removeClass("btn-primary active").addClass("btn-outline-primary");

        $(this).removeClass("btn-outline-primary").addClass("btn-primary active"); // Highlight selected filter button

        const filter =  $(this).data("filter"); // get data-filter attribute

        $(".staff-card").show();

        if (filter === "all") {
            return;  // Display all staff members if filter is all
        }

        if (filter === "active") {  // Display active staff members
            $(".staff-card").not('[data-status="active"]').hide();
        }

        else if (filter === "inactive") { // Display inactive staff members
            $(".staff-card").not('[data-status="inactive"]').hide();
        }

        else if (filter === "cashier") { // Display cashiers only
            $(".staff-card").not('[data-role="Cashier"]').hide();
        }
        else if (filter === "admin") { // Display admins only
            $(".staff-card").not('[data-role="Administrator"]').hide();
        }
    });
});
