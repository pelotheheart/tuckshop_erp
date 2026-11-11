$(function () {
    const $rows = $("#item-rows");
    const $total = $("#id_items-TOTAL_FORMS");
    const blankRow = $("#item-row-template").html().trim();

    $("#add-item").on("click", function () {
        // Rows are numbered from 0, so the new row's number is the current total.
        const index = parseInt($total.val(), 10);
        const $row = $(blankRow.replace(/__prefix__/g, index));
        $rows.append($row);
        $total.val(index + 1);
        $row.find("select").first().trigger("focus");
    });
});