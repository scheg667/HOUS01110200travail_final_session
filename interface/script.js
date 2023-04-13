const productForm = document.querySelector('#product-form');
const productContainer = document.querySelector('.product-container');
const addProductBtn = document.querySelector('#add-product');
let productCount = 1;

addProductBtn.addEventListener('click', () => {
  const newProduct = `
    <div class="product-container">
      <label for="product_id_${productCount + 1}">Product ${productCount + 1} ID:</label>
      <input type="number" id="product_id_${productCount + 1}" name="product_id_${productCount + 1}" min="1" max="50" required>
      <label for="product_quantity_${productCount + 1}">Product ${productCount + 1} Quantity:</label>
      <input type="number" id="product_quantity_${productCount + 1}" name="product_quantity_${productCount + 1}" required>
    </div>
  `;
  productContainer.insertAdjacentHTML('beforeend', newProduct);
  productCount++;
});
productForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const formData = new FormData(productForm);
  const data = {};
  for (let [key, value] of formData.entries()) {
    data[key] = parseInt(value);
  }
  new_data = {}
  if (productCount == 1) {
    new_data = {
      "product": {
        id: data.product_id_1,
        quantity: data.product_quantity_1
      }
    }
  }
  const requestOptions = {
    method: 'POST',
    mode: 'cors',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(new_data)
  };
  fetch('http:localhost:5000/order', requestOptions)
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error(error));
  productForm.reset();
  productContainer.innerHTML = `
    <div class="product-container">
      <label for="product_id_1">Product 1 ID:</label>
      <input type="number" id="product_id_1" name="product_id_1" min="1" max="50" required>
      <label for="product_quantity_1">Product 1 Quantity:</label>
      <input type="number" id="product_quantity_1" name="product_quantity_1" required>
    </div>
  `;
  productCount = 1;
});
