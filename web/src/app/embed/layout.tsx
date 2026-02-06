export default function EmbedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <>
      <style>{`header, footer, nav { display: none !important; } main { padding: 0 !important; }`}</style>
      {children}
    </>
  )
}
