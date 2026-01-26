const Navbar = document.getElementsByTagName("aside")[0];

function openNavbar() {
    console.log("open");
    Navbar.classList.remove("hidden");
}

function closeNavbar() {
    console.log(Navbar.classList.item(0));
    console.log("close");
    Navbar.classList.add("hidden");
}

function closeMessagePopUp(element) {
    element.parentElement.remove();
}
