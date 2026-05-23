/**
 * Setup global de Vitest.
 *
 * Extiende `expect` con matchers de jest-dom (toBeInTheDocument, toHaveClass, etc.)
 * y limpia el DOM despues de cada test.
 */
import "@testing-library/jest-dom/vitest"
import { afterEach } from "vitest"
import { cleanup } from "@testing-library/react"

afterEach(() => {
  cleanup()
})
