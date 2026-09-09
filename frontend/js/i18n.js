/* =====================================================================
   FR 1.4 - Bangla-first interface with an English toggle.

   How it works, in three steps:
     1. Every visible piece of text in the HTML carries a data-i18n key,
        for example  <label data-i18n="phone">
     2. TEXT holds the Bangla and English wording for each key.
     3. applyLanguage() walks the page and swaps the text.

   Bangla is the default. A new visitor sees Bangla with no action needed.
   ===================================================================== */

const TEXT = {
  bn: {
    /* general */
    appName: "হেল্পনেট",
    tagline: "একটি সমন্বিত কমিউনিটি সেবা প্ল্যাটফর্ম",
    langButton: "English",
    loading: "অপেক্ষা করুন...",
    required: "এই ঘরটি পূরণ করুন",
    networkError: "সার্ভারের সাথে সংযোগ করা যায়নি। ইন্টারনেট সংযোগ পরীক্ষা করুন।",

    /* landing */
    welcomeTitle: "হেল্পনেটে স্বাগতম",
    welcomeText: "রক্তদান, স্বেচ্ছাসেবা, কৃষিপণ্য, পুরাতন জিনিস বিনিময় এবং বর্জ্য সংগ্রহ — সব একসাথে একটি অ্যাপে।",
    goRegister: "নতুন অ্যাকাউন্ট খুলুন",
    goLogin: "লগইন করুন",

    /* register */
    registerTitle: "নতুন অ্যাকাউন্ট খুলুন",
    registerSubtitle: "মোবাইল নম্বর দিয়ে বিনামূল্যে নিবন্ধন করুন",
    fullName: "পুরো নাম",
    phone: "মোবাইল নম্বর",
    phoneHint: "উদাহরণ: ০১৭১২৩৪৫৬৭৮",
    password: "পাসওয়ার্ড",
    passwordHint: "কমপক্ষে ৮ অক্ষর, অক্ষর ও সংখ্যা মিলিয়ে",
    email: "ইমেইল",
    optional: "(ঐচ্ছিক)",
    district: "জেলা",
    upazila: "উপজেলা",
    selectDistrict: "জেলা নির্বাচন করুন",
    registerButton: "নিবন্ধন করুন",
    haveAccount: "আগে থেকে অ্যাকাউন্ট আছে?",
    loginLink: "লগইন করুন",
    registerSuccess: "নিবন্ধন সফল হয়েছে। আপনাকে ড্যাশবোর্ডে নেওয়া হচ্ছে...",

    /* login */
    loginTitle: "লগইন করুন",
    loginSubtitle: "আপনার মোবাইল নম্বর ও পাসওয়ার্ড দিন",
    loginButton: "লগইন",
    forgotPassword: "পাসওয়ার্ড ভুলে গেছেন?",
    noAccount: "অ্যাকাউন্ট নেই?",
    registerLink: "নিবন্ধন করুন",
    loginSuccess: "লগইন সফল। অপেক্ষা করুন...",

    /* forgot / reset password */
    forgotTitle: "পাসওয়ার্ড পুনরুদ্ধার",
    forgotSubtitle: "আপনার নিবন্ধিত মোবাইল নম্বর দিন, আমরা একটি কোড পাঠাব",
    sendCode: "কোড পাঠান",
    codeSent: "কোড পাঠানো হয়েছে। নিচে কোডটি লিখুন।",
    demoNote: "পরীক্ষার সংস্করণ: কোডটি সার্ভারের কনসোলে দেখানো হচ্ছে।",
    otpCode: "৬ সংখ্যার কোড",
    newPassword: "নতুন পাসওয়ার্ড",
    resetButton: "পাসওয়ার্ড পরিবর্তন করুন",
    resetSuccess: "পাসওয়ার্ড পরিবর্তন হয়েছে। এখন লগইন করুন।",
    backToLogin: "লগইনে ফিরে যান",

    /* dashboard */
    dashboardTitle: "ড্যাশবোর্ড",
    welcomeUser: "স্বাগতম",
    myProfile: "আমার তথ্য",
    name: "নাম",
    role: "ভূমিকা",
    location: "এলাকা",
    verification: "যাচাই অবস্থা",
    notVerified: "যাচাই করা হয়নি",
    verified: "যাচাইকৃত",
    logout: "লগআউট",
    services: "সেবাসমূহ",
    comingSoon: "পরবর্তী স্প্রিন্টে আসছে",
    modBlood: "রক্তদান",
    modVolunteer: "স্বেচ্ছাসেবা",
    modGoods: "পুরাতন জিনিস বিনিময়",
    modWaste: "বর্জ্য সংগ্রহ",
    modFarmer: "কৃষক বাজার",
    modHealth: "স্বাস্থ্য পরামর্শ",

    /* roles */
    role_citizen: "নাগরিক",
    role_volunteer: "স্বেচ্ছাসেবক",
    role_ngo: "সংস্থা",
    role_farmer: "কৃষক",
    role_admin: "প্রশাসক"
  },

  en: {
    appName: "HELPNET",
    tagline: "A Unified Community Services Platform",
    langButton: "বাংলা",
    loading: "Please wait...",
    required: "This field is required",
    networkError: "Could not reach the server. Please check your connection.",

    welcomeTitle: "Welcome to HELPNET",
    welcomeText: "Blood donation, volunteering, farm produce, second-hand exchange and waste collection — all in one app.",
    goRegister: "Create an account",
    goLogin: "Log in",

    registerTitle: "Create an account",
    registerSubtitle: "Register free with your mobile number",
    fullName: "Full name",
    phone: "Mobile number",
    phoneHint: "Example: 01712345678",
    password: "Password",
    passwordHint: "At least 8 characters, mixing letters and numbers",
    email: "Email",
    optional: "(optional)",
    district: "District",
    upazila: "Upazila",
    selectDistrict: "Select a district",
    registerButton: "Register",
    haveAccount: "Already have an account?",
    loginLink: "Log in",
    registerSuccess: "Registration successful. Taking you to your dashboard...",

    loginTitle: "Log in",
    loginSubtitle: "Enter your mobile number and password",
    loginButton: "Log in",
    forgotPassword: "Forgotten your password?",
    noAccount: "No account yet?",
    registerLink: "Register",
    loginSuccess: "Logged in. Please wait...",

    forgotTitle: "Reset your password",
    forgotSubtitle: "Enter your registered mobile number and we will send a code",
    sendCode: "Send code",
    codeSent: "Code sent. Enter it below.",
    demoNote: "Demo build: the code is printed in the server console.",
    otpCode: "6-digit code",
    newPassword: "New password",
    resetButton: "Change password",
    resetSuccess: "Password changed. You can now log in.",
    backToLogin: "Back to login",

    dashboardTitle: "Dashboard",
    welcomeUser: "Welcome",
    myProfile: "My details",
    name: "Name",
    role: "Role",
    location: "Area",
    verification: "Verification",
    notVerified: "Not verified",
    verified: "Verified",
    logout: "Log out",
    services: "Services",
    comingSoon: "Coming in a later sprint",
    modBlood: "Blood Donation",
    modVolunteer: "Volunteer Gathering",
    modGoods: "Second-Hand Exchange",
    modWaste: "Waste Collection",
    modFarmer: "Farmer Marketplace",
    modHealth: "Health Suggestions",

    role_citizen: "Citizen",
    role_volunteer: "Volunteer",
    role_ngo: "Organization",
    role_farmer: "Farmer",
    role_admin: "Admin"
  }
};

const LANG_KEY = "helpnet_lang";

/* Bangla is the default for anyone who has never chosen (FR 1.4). */
function getLanguage() {
  const saved = localStorage.getItem(LANG_KEY);
  return saved === "en" ? "en" : "bn";
}

function t(key) {
  const lang = getLanguage();
  return (TEXT[lang] && TEXT[lang][key]) || TEXT.bn[key] || key;
}

/* Swap every element that carries a data-i18n key. */
function applyLanguage() {
  const lang = getLanguage();
  document.documentElement.lang = lang;

  document.querySelectorAll("[data-i18n]").forEach(function (el) {
    const value = t(el.getAttribute("data-i18n"));
    if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
      el.placeholder = value;
    } else {
      el.textContent = value;
    }
  });

  document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
    el.placeholder = t(el.getAttribute("data-i18n-placeholder"));
  });

  const toggle = document.getElementById("langToggle");
  if (toggle) toggle.textContent = t("langButton");
}

/* Save the choice, update the page, and remember it on the server too
   if the user is logged in, so it follows them to another device. */
async function toggleLanguage() {
  const next = getLanguage() === "bn" ? "en" : "bn";
  localStorage.setItem(LANG_KEY, next);
  applyLanguage();

  if (typeof isLoggedIn === "function" && isLoggedIn()) {
    try {
      await apiRequest("/api/auth/language", "PUT", { preferred_language: next });
    } catch (err) {
      /* Saving the preference is not critical - the local choice still works. */
    }
  }
}

function setLanguage(lang) {
  if (lang === "bn" || lang === "en") {
    localStorage.setItem(LANG_KEY, lang);
    applyLanguage();
  }
}

document.addEventListener("DOMContentLoaded", function () {
  applyLanguage();
  const toggle = document.getElementById("langToggle");
  if (toggle) toggle.addEventListener("click", toggleLanguage);
});
