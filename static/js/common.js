class TxtType {
  constructor(el, toRotate, period) {
    this.toRotate = toRotate;         // Sare messages ka list
    this.el = el;                     // HTML element jisme text ayega
    this.loopNum = 0;                 // Kaun sa message chal raha hai
    this.period = parseInt(period);  // Har message kitni der tak rukega
    this.txt = '';                    // Abhi tak type hua text
    this.isDeleting = false;         // Delete ho raha hai ya type
    this.tick();                      // Function call karna shuru
  }

  tick() {
    const i = this.loopNum % this.toRotate.length;
    const fullTxt = this.toRotate[i];

    // Agar delete ho raha hai, to ek-ek letter hatao
    // Nahi to ek-ek letter jodte jao
    this.txt = this.isDeleting
      ? fullTxt.substring(0, this.txt.length - 1)
      : fullTxt.substring(0, this.txt.length + 1);

    this.el.querySelector('.wrap').innerHTML = this.txt;

    let delta = 150 - Math.random() * 100; // Typing speed random

    if (this.isDeleting) {
      delta /= 1; // Delete thoda fast
    }

    if (!this.isDeleting && this.txt === fullTxt) {
      delta = this.period;     // Poora likhne ke baad ruk jao
      this.isDeleting = true;  // Phir delete karna start
    } else if (this.isDeleting && this.txt === '') {
      this.isDeleting = false; // Poora delete ho gaya
      this.loopNum++;          // Agla message dikhana hai
      delta = 700;
    }

    setTimeout(() => this.tick(), delta); // Next letter ke liye wait
  }
}

// Jab page load ho, tab start karo
window.onload = function () {
  const elements = document.getElementsByClassName('typewrite');
  for (let i = 0; i < elements.length; i++) {
    const toRotate = elements[i].getAttribute('data-type');
    const period = elements[i].getAttribute('data-period');
    if (toRotate) {
      new TxtType(elements[i], JSON.parse(toRotate), period);
    }
  }
};



//menu function 

function changeMenu(){
  let main=document.getElementsByClassName('main-content')[0];
  let menu=document.getElementsByClassName('menu-content')[0];
  let footer=document.getElementsByClassName('main-footer')[0];
  if(main){
    let d=window.getComputedStyle(main).display;
    if (d==='block'){
      main.style.display='none';
      footer.style.display='none';
      menu.style.display='block';
    } else {
      menu.style.display = 'none';
      main.style.display='block';
      footer.style.display='block';
      
    }
  }else{
  }
}