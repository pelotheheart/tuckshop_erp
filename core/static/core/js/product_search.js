$(function () {
    const $search = $("#search");
    const $rows = $("#product-rows");

    // Every time the text in the search box changes...
    $search.on("input", function () {
        $.getJSON($search.data("url"), { q: $search.val() }, function (data) {
            // Clear the table, then add one row for each result Django sent back.
            $rows.empty();
            $.each(data.results, function (index, product) {
                const $tr = $("<tr>");
                $tr.append($("<td>").text(product.name));
                $tr.append($("<td>").text(product.barcode || "-"));
                $tr.append($("<td>").text("R " + product.price));

                const $stock = $("<td>").text(product.stock);
                if (product.low_stock) {
                    $stock.append(' <span class="badge text-bg-warning ms-1">Low stock</span>');
                    $tr.addClass("table-warning");
                }
                $tr.append($stock);

                $rows.append($tr);
            });
            if (data.results.length === 0) {
                $rows.append('<tr><td colspan="4">No products match.</td></tr>');
            }
        });
    });
});