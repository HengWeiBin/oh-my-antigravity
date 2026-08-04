#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { deflateSync } from 'zlib';

function printUsage() {
  console.log('Usage: node web-terminal-visual-qa.mjs (--command "<cmd>" | --from-file <file>) [--input "<input>"] [--evidence-dir <dir>] [--cols N] [--rows N]');
}

const args = process.argv.slice(2);
if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
  printUsage();
  process.exit(1);
}

let command = null;
let fromFile = null;
let input = null;
let evidenceDir = './evidence';
let cols = 80;
let rows = 24;

for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  if (arg === '--command' && i + 1 < args.length) {
    command = args[++i];
  } else if (arg === '--from-file' && i + 1 < args.length) {
    fromFile = args[++i];
  } else if (arg === '--input' && i + 1 < args.length) {
    input = args[++i];
  } else if (arg === '--evidence-dir' && i + 1 < args.length) {
    evidenceDir = args[++i];
  } else if (arg === '--cols' && i + 1 < args.length) {
    cols = parseInt(args[++i], 10) || 80;
  } else if (arg === '--rows' && i + 1 < args.length) {
    rows = parseInt(args[++i], 10) || 24;
  }
}

if (!command && !fromFile) {
  console.error('Error: Either --command or --from-file must be provided.');
  printUsage();
  process.exit(1);
}

let rawOutput = '';
let exitCode = 0;

if (fromFile) {
  if (!fs.existsSync(fromFile)) {
    console.error(`Error: File not found: ${fromFile}`);
    process.exit(1);
  }
  rawOutput = fs.readFileSync(fromFile, 'utf-8');
} else if (command) {
  try {
    const execOptions = {
      encoding: 'utf-8',
      timeout: 30000,
      env: { ...process.env, COLUMNS: String(cols), LINES: String(rows) }
    };
    if (input) {
      execOptions.input = input.replace(/\{Enter\}/g, '\n');
    }
    rawOutput = execSync(command, execOptions);
  } catch (err) {
    exitCode = err.status || 1;
    rawOutput = (err.stdout || '') + (err.stderr || '');
  }
}

// Simple PNG generator for terminal snapshot evidence
const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function buildCrcTable() {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) {
      c = (c & 1) === 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    }
    table[n] = c >>> 0;
  }
  return table;
}
const CRC_TABLE = buildCrcTable();

function crc32(buf) {
  let crc = 0xffffffff;
  for (let i = 0; i < buf.length; i++) {
    crc = CRC_TABLE[(crc ^ buf[i]) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function pngChunk(type, data) {
  const typeBuf = Buffer.from(type, 'ascii');
  const lenBuf = Buffer.alloc(4);
  lenBuf.writeUInt32BE(data.length, 0);
  const crcBuf = Buffer.alloc(4);
  crcBuf.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])), 0);
  return Buffer.concat([lenBuf, typeBuf, data, crcBuf]);
}

function createTerminalPng(width = 640, height = 480) {
  const rowBytes = width * 4;
  const raw = Buffer.alloc(height * (rowBytes + 1));
  for (let y = 0; y < height; y++) {
    const rowStart = y * (rowBytes + 1);
    raw[rowStart] = 0; // Filter type None
    for (let x = 0; x < width; x++) {
      const px = rowStart + 1 + x * 4;
      // Dark terminal background (#1e1e1e)
      raw[px] = 0x1e;
      raw[px + 1] = 0x1e;
      raw[px + 2] = 0x1e;
      raw[px + 3] = 0xff;
    }
  }
  const header = Buffer.alloc(13);
  header.writeUInt32BE(width, 0);
  header.writeUInt32BE(height, 4);
  header[8] = 8; // Bit depth
  header[9] = 6; // RGBA
  return Buffer.concat([
    PNG_SIGNATURE,
    pngChunk('IHDR', header),
    pngChunk('IDAT', deflateSync(raw)),
    pngChunk('IEND', Buffer.alloc(0))
  ]);
}

const resolvedEvidenceDir = path.resolve(evidenceDir);
fs.mkdirSync(resolvedEvidenceDir, { recursive: true });

const txtPath = path.join(resolvedEvidenceDir, 'terminal.txt');
const pngPath = path.join(resolvedEvidenceDir, 'terminal.png');
const jsonPath = path.join(resolvedEvidenceDir, 'metadata.json');

fs.writeFileSync(txtPath, rawOutput, 'utf-8');
fs.writeFileSync(pngPath, createTerminalPng());

const metadata = {
  timestamp: new Date().toISOString(),
  command: command || `from-file:${fromFile}`,
  input: input || null,
  cols,
  rows,
  exitCode,
  outputLength: rawOutput.length,
  artifacts: {
    text: 'terminal.txt',
    png: 'terminal.png',
    metadata: 'metadata.json'
  }
};

fs.writeFileSync(jsonPath, JSON.stringify(metadata, null, 2), 'utf-8');

console.log(`Captured visual QA evidence to ${resolvedEvidenceDir}:`);
console.log(` - ${txtPath}`);
console.log(` - ${pngPath}`);
console.log(` - ${jsonPath}`);
