export const escapeCsvCell = (cell: string | number): string => {
  const value = String(cell);
  const safeValue = typeof cell === 'string' && /^[\s]*[=+\-@]/.test(cell) ? `'${value}` : value;
  return `"${safeValue.replace(/"/g, '""')}"`;
};
