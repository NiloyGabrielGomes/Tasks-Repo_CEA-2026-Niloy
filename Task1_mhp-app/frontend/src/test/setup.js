import * as matchers from '@testing-library/jest-dom/matchers';

// In vitest 4.x with globals:true, expect.extend must be called inside beforeAll
// to ensure the global expect instance gets the matchers
beforeAll(() => {
  expect.extend(matchers);
});
