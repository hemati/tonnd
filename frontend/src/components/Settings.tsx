import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { KeyIcon, ClipboardDocumentIcon, TrashIcon, PlusIcon, CheckIcon } from '@heroicons/react/24/outline'
import { fetchTokens, createToken, revokeToken, type APIToken } from '../services/api'

const ALL_SCOPES = [
  { value: 'read:all', label: 'All data', description: 'Access all health data' },
  { value: 'read:vitals', label: 'Vitals', description: 'Heart rate, HRV, SpO2, breathing, VO2, temp' },
  { value: 'read:body', label: 'Body', description: 'Weight, body composition' },
  { value: 'read:sleep', label: 'Sleep', description: 'Sleep duration, stages, efficiency' },
  { value: 'read:activity', label: 'Activity', description: 'Steps, calories, active minutes' },
  { value: 'read:workouts', label: 'Workouts', description: 'Workout history, exercises, muscles' },
  { value: 'read:recovery', label: 'Recovery', description: 'Recovery score' },
]

function TokenRow({ token, onRevoke }: { token: APIToken; onRevoke: (id: string) => void }) {
  const [confirming, setConfirming] = useState(false)

  return (
    <div className={`border border-white/[.06] rounded-lg p-4 ${!token.is_active ? 'opacity-40' : ''}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <KeyIcon className="h-4 w-4 text-cyan-400 shrink-0" />
            <span className="font-medium text-sm truncate">{token.name}</span>
            {!token.is_active && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-white/30">revoked</span>
            )}
          </div>
          <div className="mt-1 font-mono text-xs text-white/25">{token.token_prefix}...</div>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {token.scopes.map((s) => (
              <span key={s} className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-400/10 text-cyan-400/70">{s}</span>
            ))}
          </div>
          <div className="mt-2 text-[11px] text-white/20">
            Created {new Date(token.created_at).toLocaleDateString()}
            {token.last_used_at && <> · Last used {new Date(token.last_used_at).toLocaleDateString()}</>}
            {token.expires_at && <> · Expires {new Date(token.expires_at).toLocaleDateString()}</>}
          </div>
        </div>
        {token.is_active && (
          <button
            onClick={() => {
              if (confirming) {
                onRevoke(token.id)
                setConfirming(false)
              } else {
                setConfirming(true)
                setTimeout(() => setConfirming(false), 3000)
              }
            }}
            className={`shrink-0 p-1.5 rounded transition-colors ${
              confirming
                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                : 'text-white/20 hover:text-white/50 hover:bg-white/5'
            }`}
            title={confirming ? 'Click again to confirm' : 'Revoke token'}
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}

function CreateTokenModal({ onClose, onCreated }: { onClose: () => void; onCreated: (raw: string) => void }) {
  const [name, setName] = useState('')
  const [selectedScopes, setSelectedScopes] = useState<string[]>(['read:all'])
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: createToken,
    onSuccess: (data) => onCreated(data.token),
    onError: (err: Error) => setError(err.message),
  })

  const toggleScope = (scope: string) => {
    if (scope === 'read:all') {
      setSelectedScopes(['read:all'])
      return
    }
    const without = selectedScopes.filter((s) => s !== 'read:all' && s !== scope)
    if (selectedScopes.includes(scope)) {
      setSelectedScopes(without.length ? without : ['read:all'])
    } else {
      setSelectedScopes([...without, scope])
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-[#111] border border-white/[.08] rounded-xl p-6 w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-semibold mb-4">Create API Token</h3>

        <label className="block text-xs text-white/40 mb-1">Token name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="My MCP Token"
          className="w-full bg-white/5 border border-white/[.08] rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-400/40 mb-4"
          autoFocus
        />

        <label className="block text-xs text-white/40 mb-2">Scopes</label>
        <div className="grid grid-cols-2 gap-2 mb-4">
          {ALL_SCOPES.map((s) => (
            <button
              key={s.value}
              onClick={() => toggleScope(s.value)}
              className={`text-left px-3 py-2 rounded-lg border text-xs transition-colors ${
                selectedScopes.includes(s.value)
                  ? 'border-cyan-400/40 bg-cyan-400/10 text-cyan-300'
                  : 'border-white/[.06] text-white/40 hover:border-white/[.12]'
              }`}
            >
              <div className="font-medium">{s.label}</div>
              <div className="text-[10px] opacity-60 mt-0.5">{s.description}</div>
            </button>
          ))}
        </div>

        {error && <div className="text-red-400 text-xs mb-3">{error}</div>}

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 text-sm rounded-lg border border-white/[.08] text-white/40 hover:text-white/60 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => mutation.mutate({ name, scopes: selectedScopes })}
            disabled={!name.trim() || mutation.isPending}
            className="flex-1 px-4 py-2 text-sm rounded-lg bg-cyan-400/15 text-cyan-300 border border-cyan-400/20 hover:bg-cyan-400/25 transition-colors disabled:opacity-30"
          >
            {mutation.isPending ? 'Creating...' : 'Create token'}
          </button>
        </div>
      </div>
    </div>
  )
}

function TokenRevealModal({ rawToken, onClose }: { rawToken: string; onClose: () => void }) {
  const [copied, setCopied] = useState(false)

  const copy = () => {
    navigator.clipboard.writeText(rawToken)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#111] border border-white/[.08] rounded-xl p-6 w-full max-w-lg mx-4">
        <div className="flex items-center gap-2 mb-3">
          <KeyIcon className="h-5 w-5 text-cyan-400" />
          <h3 className="text-lg font-semibold">Token created</h3>
        </div>

        <p className="text-xs text-amber-400/80 mb-4">
          Copy this token now. You will not be able to see it again.
        </p>

        <div className="relative">
          <pre className="bg-black/40 border border-white/[.06] rounded-lg p-3 text-xs font-mono text-cyan-300 break-all whitespace-pre-wrap pr-10">
            {rawToken}
          </pre>
          <button
            onClick={copy}
            className="absolute top-2 right-2 p-1.5 rounded-md bg-white/5 hover:bg-white/10 transition-colors"
            title="Copy to clipboard"
          >
            {copied ? <CheckIcon className="h-4 w-4 text-green-400" /> : <ClipboardDocumentIcon className="h-4 w-4 text-white/40" />}
          </button>
        </div>

        <button
          onClick={onClose}
          className="mt-4 w-full px-4 py-2 text-sm rounded-lg bg-white/5 text-white/60 hover:text-white transition-colors"
        >
          Done
        </button>
      </div>
    </div>
  )
}

export default function Settings() {
  const queryClient = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [revealToken, setRevealToken] = useState<string | null>(null)

  const { data: tokens = [], isLoading } = useQuery({
    queryKey: ['api-tokens'],
    queryFn: fetchTokens,
  })

  const revokeMutation = useMutation({
    mutationFn: revokeToken,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['api-tokens'] }),
  })

  const activeTokens = tokens.filter((t) => t.is_active)
  const revokedTokens = tokens.filter((t) => !t.is_active)

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold">API Tokens</h1>
          <p className="text-xs text-white/30 mt-1">
            Personal access tokens for the TONND API and MCP integration
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg bg-cyan-400/15 text-cyan-300 border border-cyan-400/20 hover:bg-cyan-400/25 transition-colors"
        >
          <PlusIcon className="h-4 w-4" />
          New token
        </button>
      </div>

      {isLoading ? (
        <div className="text-white/20 text-sm py-8 text-center">Loading...</div>
      ) : activeTokens.length === 0 && revokedTokens.length === 0 ? (
        <div className="border border-dashed border-white/[.08] rounded-xl py-12 text-center">
          <KeyIcon className="h-8 w-8 text-white/10 mx-auto mb-3" />
          <p className="text-sm text-white/30">No API tokens yet</p>
          <p className="text-xs text-white/15 mt-1">Create a token to access your data via API or MCP</p>
        </div>
      ) : (
        <div className="space-y-3">
          {activeTokens.map((t) => (
            <TokenRow key={t.id} token={t} onRevoke={(id) => revokeMutation.mutate(id)} />
          ))}
          {revokedTokens.length > 0 && (
            <>
              <div className="text-[11px] text-white/15 uppercase tracking-wider mt-6 mb-2">Revoked</div>
              {revokedTokens.map((t) => (
                <TokenRow key={t.id} token={t} onRevoke={() => {}} />
              ))}
            </>
          )}
        </div>
      )}

      {/* MCP Setup hint */}
      <div className="mt-8 border border-white/[.06] rounded-lg p-4">
        <h3 className="text-xs font-medium text-white/50 mb-2">MCP Setup (Claude Desktop)</h3>
        <pre className="text-[11px] text-white/25 font-mono leading-relaxed overflow-x-auto">{`{
  "mcpServers": {
    "tonnd": {
      "command": "python",
      "args": ["path/to/backend/mcp_server.py"],
      "env": {
        "TONND_API_URL": "https://tonnd.com",
        "TONND_API_TOKEN": "your_token_here"
      }
    }
  }
}`}</pre>
      </div>

      {showCreate && (
        <CreateTokenModal
          onClose={() => setShowCreate(false)}
          onCreated={(raw) => {
            setShowCreate(false)
            setRevealToken(raw)
            queryClient.invalidateQueries({ queryKey: ['api-tokens'] })
          }}
        />
      )}

      {revealToken && (
        <TokenRevealModal rawToken={revealToken} onClose={() => setRevealToken(null)} />
      )}
    </div>
  )
}
