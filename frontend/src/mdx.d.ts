declare module '*.mdx' {
  export const frontmatter: Record<string, unknown>
  const Component: React.ComponentType<{ components?: Record<string, React.ComponentType> }>
  export default Component
}
