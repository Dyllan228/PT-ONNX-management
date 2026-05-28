export function pollTask(getStatusFn, taskId, interval = 1500) {
  return new Promise((resolve, reject) => {
    const timer = setInterval(async () => {
      try {
        const res = await getStatusFn(taskId)
        const data = res.data
        if (data.status === 'completed') {
          clearInterval(timer)
          resolve(data)
        } else if (data.status === 'failed') {
          clearInterval(timer)
          reject(new Error(data.error_msg || 'Task failed'))
        }
      } catch (err) {
        clearInterval(timer)
        reject(err)
      }
    }, interval)
  })
}
