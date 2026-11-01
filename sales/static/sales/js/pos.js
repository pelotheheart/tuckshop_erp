$(function () {
    const $search = $("#pos-search");
    const $results = $("#search-results");
    const $cartRows = $("#cart-rows");
    const $total = $("#cart-total");
    const $checkout = $("#checkout");
    const $message = $("#cart-message");
    const startHint = '<tr><td colspan="4" class="text-muted">Start typing to find a product.</td></tr>';

    const cart = [];

    // Money is counted in whole cents, because JavaScript can't add amounts like 0.10 exactly.
    function toCents(price) {
        return Math.round(parseFloat(price) * 100);
    }

    function formatRand(cents) {
        return "R " + (cents / 100).toFixed(2);
    }

    function findLine(id) {
        return cart.find(function (line) { return line.id === id; });
    }

    function renderCart() {
        $cartRows.empty();
        let totalCents = 0;
        $.each(cart, function (index, line) {
            const lineCents = toCents(line.price) * line.qty;
            totalCents += lineCents;
            const $qty = $("<input>", { type: "number", class: "form-control form-control-sm text-end cart-qty", min: 1, max: line.stock, value: line.qty }).data("id", line.id);
            const $remove = $("<button>", { type: "button", class: "btn btn-sm btn-outline-danger cart-remove" }).text("×").data("id", line.id);
            const $tr = $("<tr>");
            $tr.append($("<td>").text(line.name));
            $tr.append($("<td>", { class: "text-end", style: "width: 5.5rem" }).append($qty));
            $tr.append($("<td>", { class: "text-end" }).text(formatRand(lineCents)));
            $tr.append($("<td>", { class: "text-end" }).append($remove));
            $cartRows.append($tr);
        });
        if (cart.length === 0) {
            $cartRows.append('<tr><td colspan="4" class="text-muted">The cart is empty.</td></tr>');
        }
        $total.text(formatRand(totalCents));
        $checkout.prop("disabled", cart.length === 0);
    }

    function addToCart(product) {
        $message.text("");
        const line = findLine(product.id);
        if (line && line.qty >= line.stock) {
            $message.text("Only " + line.stock + " " + line.name + " in stock.");
            return;
        }
        if (line) {
            line.qty += 1;
        } else {
            cart.push({ id: product.id, name: product.name, price: product.price, stock: product.stock, qty: 1 });
        }
        renderCart();
    }

    $search.on("input", function () {
        const q = $search.val().trim();
        if (q === "") {
            $results.html(startHint);
            return;
        }
        $.getJSON($search.data("url"), { q: q }, function (data) {
            $results.empty();
            $.each(data.results, function (index, product) {
                const $add = $("<button>", { type: "button", class: "btn btn-sm btn-primary add-to-cart" });
                if (product.stock > 0) {
                    $add.text("Add").data("product", product);
                } else {
                    $add.text("Out of stock").prop("disabled", true);
                }
                const $tr = $("<tr>");
                $tr.append($("<td>").text(product.name));
                $tr.append($("<td>", { class: "text-end" }).text("R " + product.price));
                $tr.append($("<td>", { class: "text-end" }).text(product.stock));
                $tr.append($("<td>", { class: "text-end" }).append($add));
                $results.append($tr);
            });
            if (data.results.length === 0) {
                $results.append('<tr><td colspan="4" class="text-muted">No products match.</td></tr>');
            }
        });
    });

    // The Add buttons don't exist when the page loads, so the click is listened for on the table instead.
    $results.on("click", ".add-to-cart", function () {
        addToCart($(this).data("product"));
        $search.val("").focus();
        $results.html(startHint);
    });

    $cartRows.on("change", ".cart-qty", function () {
        const line = findLine($(this).data("id"));
        let qty = parseInt($(this).val(), 10);
        $message.text("");
        if (isNaN(qty) || qty < 1) {
            qty = 1;
        } else if (qty > line.stock) {
            qty = line.stock;
            $message.text("Only " + line.stock + " " + line.name + " in stock.");
        }
        line.qty = qty;
        renderCart();
    });

    $cartRows.on("click", ".cart-remove", function () {
        cart.splice(cart.indexOf(findLine($(this).data("id"))), 1);
        $message.text("");
        renderCart();
    });
        $checkout.on("click", function () {
        const items = $.map(cart, function (line) {
            return { id: line.id, qty: line.qty };
        });
        // Switched off straight away, so a double click can't send the sale twice.
        $checkout.prop("disabled", true);
        $message.text("");
        $.ajax({
            url: $checkout.data("url"),
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ items: items }),
        }).done(function (data) {
            window.location.href = data.receipt_url;
        }).fail(function (xhr) {
            const error = xhr.responseJSON ? xhr.responseJSON.error : "The sale couldn't be saved. Check your connection and try again.";
            $message.text(error);
            $checkout.prop("disabled", false);
        });
    });
});