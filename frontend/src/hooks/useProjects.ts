import { useEffect } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { projectApi } from '@/services/api'
import type { Project } from '@/types'

/**
 * Hook to fetch and manage projects
 */
export function useProjects() {
  const { projects, setProjects, currentProject, setCurrentProject } = useAppStore()

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const fetchedProjects = await projectApi.getProjects()
        setProjects(fetchedProjects)
        
        // Set first project as current if no current project
        if (!currentProject && fetchedProjects.length > 0) {
          setCurrentProject(fetchedProjects[0])
        }
      } catch (error) {
        console.error('Failed to fetch projects:', error)
      }
    }

    if (projects.length === 0) {
      fetchProjects()
    }
  }, [projects.length, setProjects, currentProject, setCurrentProject])

  const createProject = async (name: string, description?: string) => {
    try {
      const newProject = await projectApi.createProject({ name, description })
      setProjects([...projects, newProject])
      setCurrentProject(newProject)
      return newProject
    } catch (error) {
      console.error('Failed to create project:', error)
      throw error
    }
  }

  const deleteProject = async (projectId: string) => {
    try {
      await projectApi.deleteProject(projectId)
      const updatedProjects = projects.filter(p => p.id !== projectId)
      setProjects(updatedProjects)
      
      // If deleted project was current, set another one or null
      if (currentProject?.id === projectId) {
        setCurrentProject(updatedProjects.length > 0 ? updatedProjects[0] : null)
      }
    } catch (error) {
      console.error('Failed to delete project:', error)
      throw error
    }
  }

  const refreshProjects = async () => {
    try {
      const fetchedProjects = await projectApi.getProjects()
      setProjects(fetchedProjects)
    } catch (error) {
      console.error('Failed to refresh projects:', error)
      throw error
    }
  }

  return {
    projects,
    currentProject,
    createProject,
    deleteProject,
    refreshProjects,
    setCurrentProject,
  }
}

