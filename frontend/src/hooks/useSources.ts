import { useEffect, useState } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { fileApi } from '@/services/api'
import type { Source, SourceStats, FileDetails, SearchInFileRequest, SearchInFileResponse } from '@/types'

/**
 * Hook to fetch and manage sources (similar to gemini-file-search.py)
 * Sources are attached to conversation (like NotebookLM)
 */
export function useSources(projectId: string | null, conversationId: string | null = null) {
  const { sources, setSources, removeSource: removeSourceFromStore } = useAppStore()
  const [isLoading, setIsLoading] = useState(false)
  const [stats, setStats] = useState<SourceStats | null>(null)

  useEffect(() => {
    if (!projectId) {
      setSources([])
      return
    }

    const fetchSources = async () => {
      try {
        setIsLoading(true)
        const fetchedSources = await fileApi.getSources(projectId, conversationId || undefined)
        setSources(fetchedSources)
      } catch (error) {
        console.error('Failed to fetch sources:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchSources()
  }, [projectId, conversationId, setSources])

  const fetchStats = async () => {
    if (!projectId) return null

    try {
      const fetchedStats = await fileApi.getSourceStats(projectId)
      setStats(fetchedStats)
      return fetchedStats
    } catch (error) {
      console.error('Failed to fetch stats:', error)
      return null
    }
  }

  const getFileDetails = async (sourceId: string): Promise<FileDetails | null> => {
    if (!projectId) return null

    try {
      const details = await fileApi.getSourceDetails(sourceId, projectId)
      return details
    } catch (error) {
      console.error('Failed to get file details:', error)
      return null
    }
  }

  const searchInFile = async (
    sourceId: string,
    request: SearchInFileRequest
  ): Promise<SearchInFileResponse | null> => {
    if (!projectId) return null

    try {
      const result = await fileApi.searchInFile(sourceId, projectId, request)
      return result
    } catch (error) {
      console.error('Failed to search in file:', error)
      return null
    }
  }

  const rebuildIndex = async (force: boolean = false): Promise<SourceStats | null> => {
    if (!projectId) return null

    try {
      const result = await fileApi.rebuildIndex(projectId, force)
      // Refresh sources and stats after rebuild
      await refreshSources()
      await fetchStats()
      return result.stats
    } catch (error) {
      console.error('Failed to rebuild index:', error)
      return null
    }
  }

  const deleteSource = async (sourceId: string) => {
    if (!projectId) return

    try {
      await fileApi.deleteSource(sourceId, projectId, conversationId || undefined)
      removeSourceFromStore(sourceId)
      // Refresh stats after deletion
      await fetchStats()
    } catch (error) {
      console.error('Failed to delete source:', error)
      throw error
    }
  }

  const refreshSources = async () => {
    if (!projectId) return
    try {
      setIsLoading(true)
      const fetchedSources = await fileApi.getSources(projectId, conversationId || undefined)
      setSources(fetchedSources)
    } catch (error) {
      console.error('Failed to refresh sources:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return {
    sources: sources.filter(s => s.id), // Filter valid sources
    isLoading,
    stats,
    deleteSource,
    refreshSources,
    fetchStats,
    getFileDetails,
    searchInFile,
    rebuildIndex,
  }
}

