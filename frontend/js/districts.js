/* The 64 districts of Bangladesh.

   Kept in one file so every module that needs a location (blood matching,
   farmer listings, waste pickup) uses the SAME spelling. Inconsistent
   spelling would silently break "nearby" matching later.                */

const DISTRICTS = [
  "Bagerhat","Bandarban","Barguna","Barishal","Bhola","Bogura","Brahmanbaria",
  "Chandpur","Chattogram","Chuadanga","Cox's Bazar","Cumilla","Dhaka","Dinajpur",
  "Faridpur","Feni","Gaibandha","Gazipur","Gopalganj","Habiganj","Jamalpur",
  "Jashore","Jhalokati","Jhenaidah","Joypurhat","Khagrachhari","Khulna",
  "Kishoreganj","Kurigram","Kushtia","Lakshmipur","Lalmonirhat","Madaripur",
  "Magura","Manikganj","Meherpur","Moulvibazar","Munshiganj","Mymensingh",
  "Naogaon","Narail","Narayanganj","Narsingdi","Natore","Nawabganj","Netrokona",
  "Nilphamari","Noakhali","Pabna","Panchagarh","Patuakhali","Pirojpur",
  "Rajbari","Rajshahi","Rangamati","Rangpur","Satkhira","Shariatpur","Sherpur",
  "Sirajganj","Sunamganj","Sylhet","Tangail","Thakurgaon"
];

function populateDistricts(selectId) {
  const select = document.getElementById(selectId);
  if (!select) return;
  DISTRICTS.forEach(function (name) {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    select.appendChild(option);
  });
}
