import { useEffect, useState } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { fileApi } from '@/services/api'
import type { SourceStats, FileDetails, SearchInFileRequest, SearchInFileResponse } from '@/types'

/**
 * Hook to fetch and manage sources
 */
export function useSources(conversationId: string | null = null) {
  const { sources, setSources, removeSource: removeSourceFromStore } = useAppStore()
  const [isLoading, setIsLoading] = useState(false)
  const [stats, setStats] = useState<SourceStats | null>(null)

  useEffect(() => {
    const fetchSources = async () => {
      try {
        setIsLoading(true)
        const fetchedSources = await fileApi.getSources(conversationId || undefined)
        setSources(fetchedSources)
      } catch (error) {
        console.error('Failed to fetch sources:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchSources()
  }, [conversationId, setSources])

  const fetchStats = async () => {
    try {
      const fetchedStats = await fileApi.getSourceStats()
      setStats(fetchedStats)
      return fetchedStats
    } catch (error) {
      console.error('Failed to fetch stats:', error)
      return null
    }
  }

  const getFileDetails = async (sourceId: string): Promise<FileDetails | null> => {
    try {
      const details = await fileApi.getSourceDetails(sourceId)
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
    try {
      const result = await fileApi.searchInFile(sourceId, request)
      return result
    } catch (error) {
      console.error('Failed to search in file:', error)
      return null
    }
  }

  const rebuildIndex = async (force: boolean = false): Promise<SourceStats | null> => {
    try {
      const result = await fileApi.rebuildIndex(force)
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
    try {
      await fileApi.deleteSource(sourceId, conversationId || undefined)
      removeSourceFromStore(sourceId)
      // Refresh stats after deletion
      await fetchStats()
    } catch (error) {
      console.error('Failed to delete source:', error)
      throw error
    }
  }

  const refreshSources = async () => {
    try {
      setIsLoading(true)
      const fetchedSources = await fileApi.getSources(conversationId || undefined)
      setSources(fetchedSources)
    } catch (error) {
      console.error('Failed to refresh sources:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return {
    sources,
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

