/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#f4f8ff",
        ink: "#173a5e",
        muted: "#445066",
        accent: "#ffb347"
      },
      boxShadow: {
        card: "0 20px 60px rgba(20, 40, 80, 0.15)"
      },
      borderRadius: {
        card: "28px"
      }
    }
  },
  plugins: []
};

