// document.addEventListener('DOMContentLoaded', function() {
//     var accordions = document.getElementsByClassName('accordion');
    
//     for (var i = 0; i < accordions.length; i++) {
//         accordions[i].addEventListener('click', function() {
//             this.classList.toggle('active');
//             var panel = this.nextElementSibling;
//             if (panel.style.display === "block") {
//                 panel.style.display = "none";
//             } else {
//                 panel.style.display = "block";
//             }
//         });
//     }
// });

  // window.onbeforeunload = function () {
  //   window.scrollTo(0, 0);
  // };

 

// ==============================================================

  let lastScrollY = window.scrollY;
  const header = document.querySelector("#nav-bar");

  window.addEventListener("scroll", () => {
    if (window.scrollY > lastScrollY) {
      // User is scrolling down, hide the header
      header.style.top = "-80px"; // Adjust based on header height
    } else {
      // User is scrolling up, show the header
      header.style.top = "0";
    }
    lastScrollY = window.scrollY;
  });

  // =========================================
 
  var profileCards = document.getElementsByClassName("suc-profile-card");

  for (var i = 0; i < profileCards.length; i++) {
    profileCards[i].addEventListener("click", function() {
      var content = this.querySelector(".suc-accordion-content");
      if (content.style.maxHeight) {
        content.style.maxHeight = null;
      } else {
        content.style.maxHeight = content.scrollHeight + "px";
      }
    });
  }


// ================================================================
// Show the button when scrolled down
window.onscroll = function () {
  const button = document.getElementById("top-button");
  if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
    button.style.display = "block"; // Show button
  } else {
    button.style.display = "none"; // Hide button
  }
};

// Scroll to top when the button is clicked
function scrollToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" }); // Smooth scrolling
}


// --------------------------------------------------------
