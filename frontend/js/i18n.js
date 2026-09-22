/* ============================================================
   HELPNET - FR 1.4
   Bangla / English Language Toggle
   ============================================================ */

const TEXT = {

    /* =========================
       BANGLA
       ========================= */
    bn: {

        appName: "হেল্পনেট",

        /* Home */
        homeSubtitle: "সংযুক্ত হোন। সাহায্য করুন। ভাগ করুন।",

        welcomeText:
            "আপনার সম্প্রদায়ের মানুষের সাথে সংযুক্ত হয়ে সাহায্য, সেবা ও সম্পদ ভাগ করে নিন।",

        goLogin: "লগইন করুন",

        goRegister: "নতুন অ্যাকাউন্ট তৈরি করুন",

        tagline:
            "HELPNET — একটি সমন্বিত কমিউনিটি সেবা প্ল্যাটফর্ম",


        /* Register */
        registerTitle: "নতুন অ্যাকাউন্ট খুলুন",

        registerSubtitle:
            "মোবাইল নম্বর দিয়ে বিনামূল্যে নিবন্ধন করুন",

        fullName: "পুরো নাম",

        phone: "মোবাইল নম্বর",

        phoneHint: "উদাহরণ: ০১৭১২৩৪৫৬৭৮",

        password: "পাসওয়ার্ড",

        passwordHint:
            "কমপক্ষে ৮ অক্ষর, অক্ষর ও সংখ্যা মিলিয়ে",

        email: "ইমেইল",

        optional: "(ঐচ্ছিক)",

        role: "ভূমিকা",

        selectRole: "ভূমিকা নির্বাচন করুন",

        district: "জেলা",

        upazila: "উপজেলা",

        selectDistrict: "জেলা নির্বাচন করুন",

        registerButton: "নিবন্ধন করুন",

        haveAccount: "আগে থেকে অ্যাকাউন্ট আছে?",

        loginLink: "লগইন করুন",


        /* Login */
        loginTitle: "লগইন করুন",

        loginSubtitle:
            "আপনার মোবাইল নম্বর ও পাসওয়ার্ড দিন",

        loginButton: "লগইন",

        forgotPassword: "পাসওয়ার্ড ভুলে গেছেন?",

        noAccount: "অ্যাকাউন্ট নেই?",

        registerLink: "নিবন্ধন করুন",


        /* Dashboard */
        dashboardTitle: "ড্যাশবোর্ড",

        welcomeUser: "স্বাগতম",

        myProfile: "আমার তথ্য",

        name: "নাম",

        location: "এলাকা",

        verification: "যাচাই অবস্থা",

        notVerified: "যাচাই করা হয়নি",

        verified: "যাচাইকৃত",

        logout: "লগআউট",

        services: "সেবাসমূহ",

        comingSoon: "পরবর্তী স্প্রিন্টে আসছে",


        /* Services */
        modBlood: "রক্তদান",

        modVolunteer: "স্বেচ্ছাসেবা",

        modGoods: "পুরাতন জিনিস বিনিময়",

        modWaste: "বর্জ্য সংগ্রহ",

        modFarmer: "কৃষক বাজার",

        modHealth: "স্বাস্থ্য পরামর্শ",


        /* Roles */
        role_citizen: "নাগরিক",

        role_volunteer: "স্বেচ্ছাসেবক",

        role_ngo: "সংস্থা",

        role_farmer: "কৃষক",

        role_admin: "প্রশাসক",


        /* Language button */
        langButton: "English"
    },


    /* =========================
       ENGLISH
       ========================= */
    en: {

        appName: "HELPNET",
         tagline: "A Unified Community Services Platform",

        /* Home */
        homeSubtitle: "Connect. Help. Share.",

        welcomeText:
            "Connect with people in your community and share help, services and resources.",

        goLogin: "Log in",

        goRegister: "Create an account",

        tagline:
            "HELPNET — A Unified Community Services Platform",


        /* Register */
        registerTitle: "Create an account",

        registerSubtitle:
            "Register free with your mobile number",

        fullName: "Full name",

        phone: "Mobile number",

        phoneHint: "Example: 01712345678",

        password: "Password",

        passwordHint:
            "At least 8 characters, mixing letters and numbers",

        email: "Email",

        optional: "(optional)",

        role: "Role",

        selectRole: "Select your role",

        district: "District",

        upazila: "Upazila",

        selectDistrict: "Select a district",

        registerButton: "Register",

        haveAccount: "Already have an account?",

        loginLink: "Log in",


        /* Login */
        loginTitle: "Log in",

        loginSubtitle:
            "Enter your mobile number and password",

        loginButton: "Log in",

        forgotPassword: "Forgot your password?",

        noAccount: "Don't have an account?",

        registerLink: "Register",


        /* Dashboard */
        dashboardTitle: "Dashboard",

        welcomeUser: "Welcome",

        myProfile: "My details",

        name: "Name",

        location: "Area",

        verification: "Verification",

        notVerified: "Not verified",

        verified: "Verified",

        logout: "Log out",

        services: "Services",

        comingSoon: "Coming in a later sprint",


        /* Services */
        modBlood: "Blood Donation",

        modVolunteer: "Volunteer Gathering",

        modGoods: "Second-Hand Exchange",

        modWaste: "Waste Collection",

        modFarmer: "Farmer Marketplace",

        modHealth: "Health Suggestions",


        /* Roles */
        role_citizen: "Citizen",

        role_volunteer: "Volunteer",

        role_ngo: "Organization",

        role_farmer: "Farmer",

        role_admin: "Admin",


        /* Language button */
        langButton: "বাংলা"
    }
};


/* ============================================================
   STORAGE
   ============================================================ */

const LANG_KEY = "helpnet_lang";


/* ============================================================
   GET CURRENT LANGUAGE
   ============================================================ */

function getLanguage() {

    const savedLanguage = localStorage.getItem(LANG_KEY);

    if (savedLanguage === "en") {
        return "en";
    }

    return "bn";
}


/* ============================================================
   GET TRANSLATION
   ============================================================ */

function t(key) {

    const language = getLanguage();

    if (
        TEXT[language] &&
        TEXT[language][key]
    ) {
        return TEXT[language][key];
    }

    if (TEXT.bn[key]) {
        return TEXT.bn[key];
    }

    return key;
}


/* ============================================================
   APPLY LANGUAGE
   ============================================================ */

function applyLanguage() {

    const language = getLanguage();

    console.log("HELPNET language:", language);

    /* Change HTML language */
    document.documentElement.lang = language;


    /* -----------------------------------------
       Normal text
       ----------------------------------------- */

    const elements = document.querySelectorAll("[data-i18n]");

    console.log(
        "HELPNET translation elements:",
        elements.length
    );


    elements.forEach(function (element) {

        const key = element.getAttribute("data-i18n");

        const translation = t(key);

        if (
            element.tagName === "INPUT" ||
            element.tagName === "TEXTAREA"
        ) {

            element.placeholder = translation;

        } else {

            element.textContent = translation;

        }

    });


    /* -----------------------------------------
       Placeholder translations
       ----------------------------------------- */

    const placeholderElements =
        document.querySelectorAll(
            "[data-i18n-placeholder]"
        );


    placeholderElements.forEach(function (element) {

        const key =
            element.getAttribute(
                "data-i18n-placeholder"
            );

        element.placeholder = t(key);

    });


    /* -----------------------------------------
       Language button
       ----------------------------------------- */

    const button =
        document.getElementById("langToggle");


    if (button) {

        button.textContent =
            t("langButton");

    }

}


/* ============================================================
   TOGGLE LANGUAGE
   ============================================================ */

function toggleLanguage() {

    const currentLanguage = getLanguage();

    let newLanguage;

    if (currentLanguage === "bn") {

        newLanguage = "en";

    } else {

        newLanguage = "bn";

    }


    console.log(
        "Changing language:",
        currentLanguage,
        "→",
        newLanguage
    );


    /* Save language */
    localStorage.setItem(
        LANG_KEY,
        newLanguage
    );


    /* Apply immediately */
    applyLanguage();

}


/* ============================================================
   SET LANGUAGE
   ============================================================ */

function setLanguage(language) {

    if (
        language !== "bn" &&
        language !== "en"
    ) {

        return;

    }


    localStorage.setItem(
        LANG_KEY,
        language
    );


    applyLanguage();

}


/* ============================================================
   PAGE LOAD
   ============================================================ */

function initializeI18n() {

        console.log(
            "HELPNET i18n.js loaded successfully"
        );


        /* Apply default language */
        applyLanguage();


        /* Language button */
        const button =
            document.getElementById(
                "langToggle"
            );


        if (button) {

            button.addEventListener(
                "click",
                toggleLanguage
            );

            console.log(
                "HELPNET language button connected"
            );

        } else {

            console.error(
                "HELPNET: langToggle button not found"
            );

        }

}

/* The home page loads this script at the end of <body>, while other
   pages may load it after DOMContentLoaded. Support both cases. */
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeI18n, { once: true });
} else {
    initializeI18n();
}
