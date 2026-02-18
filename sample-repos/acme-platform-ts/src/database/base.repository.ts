import { Repository, FindOptionsWhere, IsNull } from 'typeorm';
import { Injectable } from '@nestjs/common';

/**
 * AcmeSoftDeleteEntity — base entity mixin for Acme soft-delete policy.
 * Acme standard: NEVER hard-delete records.
 */
export interface AcmeSoftDeleteEntity {
  id: string;
  deletedAt: Date | null;
  deletedBy: string | null;
}

/**
 * AcmeBaseRepository — base repository for all TypeORM entities in Acme services.
 * Enforces soft-delete and provides standard CRUD operations.
 *
 * Usage:
 *   @Injectable()
 *   export class UserRepository extends AcmeBaseRepository<UserEntity> {
 *     constructor(@InjectRepository(UserEntity) repo: Repository<UserEntity>) {
 *       super(repo);
 *     }
 *   }
 */
@Injectable()
export class AcmeBaseRepository<T extends AcmeSoftDeleteEntity> {
  constructor(protected readonly repository: Repository<T>) {}

  async findById(id: string): Promise<T | null> {
    return this.repository.findOne({
      where: { id, deletedAt: IsNull() } as FindOptionsWhere<T>,
    });
  }

  async findAll(limit: number = 100, offset: number = 0): Promise<T[]> {
    return this.repository.find({
      where: { deletedAt: IsNull() } as FindOptionsWhere<T>,
      take: limit,
      skip: offset,
    });
  }

  async softDelete(id: string, deletedBy: string): Promise<boolean> {
    const result = await this.repository.update(
      { id, deletedAt: IsNull() } as FindOptionsWhere<T>,
      { deletedAt: new Date(), deletedBy } as any,
    );
    return (result.affected ?? 0) > 0;
  }

  async save(entity: T): Promise<T> {
    return this.repository.save(entity);
  }
}
