module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  rules: {
    '@typescript-eslint/ban-ts-comment': 'off',
    'no-useless-escape': 0,
    'prefer-const': 0,
    'react/prop-types': 0,
    'react/display-name': 0
  },
  plugins: [
    '@typescript-eslint',
    'react'
  ],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended'
  ],
};