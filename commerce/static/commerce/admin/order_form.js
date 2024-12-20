document.addEventListener("DOMContentLoaded", function () {
  const editionField = document.getElementById("id_edition");
  const boxField = document.getElementById("id_box");

  editionField.addEventListener("change", function () {
    const editionId = this.value;
    if (!editionId) {
      boxField.innerHTML = '<option value="">---------</option>';
      return;
    }

    fetch(`/admin/commerce/order/boxes/${editionId}/`)
      .then((response) => response.json())
      .then((data) => {
        boxField.innerHTML = '<option value="">---------</option>';
        data.forEach((box) => {
          const option = document.createElement("option");
          option.value = box.id;
          option.textContent = `Box N°: ${box.ordinal}`;
          boxField.appendChild(option);
        });
      });
  });
});
