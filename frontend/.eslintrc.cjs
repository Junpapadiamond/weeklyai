module.exports = {
  root: true,
  env: {
    es2021: true,
  },
  extends: ['eslint:recommended'],
  parserOptions: {
    ecmaVersion: 2021,
    sourceType: 'script',
  },
  ignorePatterns: ['public/gifs/**', 'public/art/**'],
  overrides: [
    {
      files: ['public/js/**/*.js'],
      env: {
        browser: true,
      },
      globals: {
        p5: 'readonly',
      },
    },
    {
      files: ['app.js'],
      env: {
        node: true,
      },
    },
  ],
};
